import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from services.agent.master import run_fashion_agent
from services.api.core.database import SessionLocal, get_db
from services.api.core.moderation import moderate_text
from services.api.services.orchestrator import run_design_session
from services.api.core.models import Conversation, Session
from services.api.core.redis_client import get_redis
from services.api.core.rate_limit import limiter
from services.api.core.security import get_current_user_id
from services.api.services.asr import transcribe_audio
from services.api.services.tts import synthesize_speech

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    language: str = "te"


class ChatMessageResponse(BaseModel):
    session_id: str
    reply: str
    intent: str
    language: str
    audio_base64: str | None = None
    outfits: dict | None = None
    products: list | None = None
    tailoring_pdf_base64: str | None = None


async def _persist_turn(db: AsyncSession, session_id: str, role: str, content: str, language: str) -> None:
    db.add(Conversation(session_id=session_id, role=role, content=content, language=language))
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
        )

    session_id = body.session_id or str(uuid.uuid4())
    if not body.session_id:
        db.add(Session(id=session_id, user_id=user_id))
        await db.commit()

    redis = get_redis()
    history_key = f"chat:{session_id}:history"
    raw_history = await redis.lrange(history_key, 0, 19)
    history = [json.loads(h) for h in raw_history]

    outfits_payload = None
    products_payload = None
    tailoring_b64 = None

    result = await run_fashion_agent(body.message, history=history, language=body.language)
    reply = result["reply"]
    intent = result["intent"]

    if intent == "design_request":
        flow = await run_design_session(body.message, history=history, language=body.language)
        outfits_payload = flow.get("outfits")
        products_payload = flow.get("products")
        tailoring_b64 = flow.get("tailoring_pdf_base64")

    await _persist_turn(db, session_id, "user", body.message, body.language)
    await _persist_turn(db, session_id, "assistant", reply, body.language)

    await redis.rpush(history_key, json.dumps({"role": "user", "content": body.message}))
    await redis.rpush(history_key, json.dumps({"role": "assistant", "content": reply}))
    await redis.expire(history_key, 86400)

    audio_b64 = await synthesize_speech(reply, language=body.language)
    return ChatMessageResponse(
        session_id=session_id,
        reply=reply,
        intent=intent,
        language=body.language,
        audio_base64=audio_b64,
        outfits=outfits_payload,
        products=products_payload,
        tailoring_pdf_base64=tailoring_b64,
    )


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    redis = get_redis()
    history_key = f"chat:{session_id}:history"

    try:
        while True:
            data = await websocket.receive()
            language = "te"
            if "bytes" in data and data["bytes"]:
                text = await transcribe_audio(data["bytes"])
                await websocket.send_json({"type": "transcript", "text": text})
                message = text
            elif "text" in data and data["text"]:
                payload = json.loads(data["text"])
                message = payload.get("message", "")
                language = payload.get("language", "te")
            else:
                continue

            raw_history = await redis.lrange(history_key, 0, 19)
            history = [json.loads(h) for h in raw_history]
            result = await run_fashion_agent(message, history=history, language=language)
            reply = result["reply"]

            await redis.rpush(history_key, json.dumps({"role": "user", "content": message}))
            await redis.rpush(history_key, json.dumps({"role": "assistant", "content": reply}))
            await redis.expire(history_key, 86400)

            async with SessionLocal() as db:
                await _persist_turn(db, session_id, "user", message, language)
                await _persist_turn(db, session_id, "assistant", reply, language)

            await websocket.send_json({"type": "reply", "text": reply, "intent": result["intent"]})
            audio_b64 = await synthesize_speech(reply, language=language)
            if audio_b64:
                await websocket.send_json({"type": "audio", "data": audio_b64})
    except WebSocketDisconnect:
        pass
