import json
import uuid
import base64
from typing import Any

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.agent.graph import run_graph
from services.api.core.database import SessionLocal, get_db
from services.api.core.moderation import moderate_text
from services.api.core.models import Conversation, Session
from services.api.core.rate_limit import limiter
from services.api.core.security import get_current_user_id
from services.api.services.asr import transcribe_audio
from services.api.services.tts import synthesize_speech

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    language: str = "te"
    image_base64: str | None = None


class ChatMessageResponse(BaseModel):
    session_id: str
    reply: str
    intent: str
    language: str
    audio_base64: str | None = None
    outfits: dict | None = None
    products: list | None = None
    tailoring_pdf_base64: str | None = None
    composite_image_b64: str | None = None
    status: str
    error: str | None = None


async def _persist_turn(db: AsyncSession, session_id: str, role: str, content: str, language: str, metadata: dict | None = None) -> None:
    db.add(Conversation(session_id=session_id, role=role, content=content, language=language, metadata_json=metadata))
    await db.commit()


@router.post("/message", response_model=ChatMessageResponse)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    body: ChatMessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    ok, block_reason = moderate_text(body.message)
    if not ok:
        return ChatMessageResponse(
            session_id=body.session_id or str(uuid.uuid4()),
            reply=block_reason or "Blocked",
            intent="blocked",
            language=body.language,
            status="active",
        )

    session_id = body.session_id or str(uuid.uuid4())
    if not body.session_id:
        db.add(Session(id=session_id, user_id=user_id, status="active"))
        await db.commit()
    else:
        # Load session to check if finalized
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalars().first()
        if session and session.status == "finalized":
            # Force a new session since this one is finalized (or user can explicitly resume, but default to new)
            if "resume" not in body.message.lower():
                 session_id = str(uuid.uuid4())
                 db.add(Session(id=session_id, user_id=user_id, status="active"))
                 await db.commit()

    # The graph now handles loading history, state, and planning
    result = await run_graph(
        message=body.message,
        user_id=user_id,
        session_id=session_id,
        language=body.language,
        image_b64=body.image_base64
    )

    reply = result["reply"]
    intent = result["intent"]
    
    # Save the turn to DB explicitly with metadata
    metadata = {
        "intent": intent,
        "outfits": result.get("outfits"),
        "products": result.get("products"),
        "composite_image_b64": result.get("composite_image_b64")
    }
    await _persist_turn(db, session_id, "user", body.message, body.language)
    await _persist_turn(db, session_id, "assistant", reply, body.language, metadata)

    audio_b64 = await synthesize_speech(reply, language=body.language)
    
    return ChatMessageResponse(
        session_id=session_id,
        reply=reply,
        intent=intent,
        language=body.language,
        audio_base64=audio_b64,
        outfits={"variants": result.get("outfits", [])} if result.get("outfits") else None,
        products=result.get("products"),
        tailoring_pdf_base64=result.get("tailoring_pdf_base64"),
        composite_image_b64=result.get("composite_image_b64"),
        status=result.get("status", "active"),
        error=result.get("error")
    )


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    user_id = "ws_user" # We need actual auth for WS in production, mocking for now.
    
    async with SessionLocal() as db:
        result = await db.execute(select(Session).where(Session.id == session_id))
        if not result.scalars().first():
             db.add(Session(id=session_id, user_id=user_id, status="active"))
             await db.commit()

    try:
        while True:
            data = await websocket.receive()
            language = "te"
            image_b64 = None
            
            if "bytes" in data and data["bytes"]:
                text = await transcribe_audio(data["bytes"])
                await websocket.send_json({"type": "transcript", "text": text})
                message = text
            elif "text" in data and data["text"]:
                payload = json.loads(data["text"])
                message = payload.get("message", "")
                language = payload.get("language", "te")
                image_b64 = payload.get("image_base64")
            else:
                continue

            result = await run_graph(
                message=message,
                user_id=user_id,
                session_id=session_id,
                language=language,
                image_b64=image_b64
            )

            reply = result["reply"]

            async with SessionLocal() as db:
                metadata = {
                    "intent": result["intent"],
                    "outfits": result.get("outfits"),
                    "products": result.get("products"),
                    "composite_image_b64": result.get("composite_image_b64")
                }
                await _persist_turn(db, session_id, "user", message, language)
                await _persist_turn(db, session_id, "assistant", reply, language, metadata)

            response_payload = {
                "type": "reply", 
                "text": reply, 
                "intent": result["intent"],
                "outfits": result.get("outfits"),
                "composite_image": result.get("composite_image_b64"),
                "status": result.get("status")
            }
            if result.get("error"):
                response_payload["error"] = result["error"]
                
            await websocket.send_json(response_payload)
            
            audio_b64 = await synthesize_speech(reply, language=language)
            if audio_b64:
                await websocket.send_json({"type": "audio", "data": audio_b64})
    except WebSocketDisconnect:
        pass
