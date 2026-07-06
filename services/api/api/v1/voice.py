"""Voice conversation endpoint — Groq Whisper ASR → Stylist LLM → Sarvam TTS.

POST /api/v1/voice/converse: Full voice loop for outfit negotiation.
POST /api/v1/voice/converse-text: Text-based fallback.
POST /api/v1/voice/finalize: Finalize outfit → generate image → save to wardrobe.
"""

import base64
import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.core.database import get_db
from services.api.core.models import BodyProfile, WardrobeItem, Conversation, Session as DbSession
from services.api.core.security import get_current_user_id
from services.api.services.sarvam_client import (
    synthesize_with_fallback,
    transcribe_with_fallback,
)
from services.agent.stylist import (
    OutfitStage,
    get_or_create_session,
    get_session,
    stylist_respond,
)

logger = logging.getLogger(__name__)

router = APIRouter()

async def _ensure_db_session(db: AsyncSession, session_id: str, user_id: str):
    db_session = await db.get(DbSession, session_id)
    if not db_session:
        db.add(DbSession(id=session_id, user_id=user_id))
        try:
            await db.commit()
        except Exception:
            await db.rollback()

async def _load_history_if_needed(db: AsyncSession, session_id: str):
    """Load conversation history from DB into memory if memory is empty."""
    session = get_or_create_session(session_id)
    if not session.history:
        from sqlalchemy import select
        from services.api.core.models import Conversation
        result = await db.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(Conversation.created_at.asc())
        )
        for msg in result.scalars().all():
            session.history.append({"role": msg.role, "content": msg.content})


class ConverseResponse(BaseModel):
    transcript: str
    reply_text: str
    reply_audio_b64: str | None
    detected_language: str
    asr_engine: str
    tts_engine: str
    outfit_state: dict


@router.post("/converse", response_model=ConverseResponse)
async def voice_converse(
    audio: UploadFile = File(...),
    session_id: str = Form("default"),
    language: str = Form(""),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Full voice conversation loop: ASR → LLM stylist → TTS → response.

    Accepts audio blob + session_id, returns transcript, reply text,
    reply audio as base64, detected language, and engine info.
    Language is auto-detected if not provided.
    """
    # Read and validate audio
    audio_bytes = await audio.read()
    if len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Audio too short")
    if len(audio_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio too large (max 10MB)")

    # Isolate session per user
    session_id = f"{user_id}-{session_id}"

    # Step 1: ASR — Groq Whisper (primary) → Sarvam → HF Whisper
    try:
        transcript, detected_lang, asr_engine = await transcribe_with_fallback(
            audio_bytes, language=language if language else None,
        )
    except RuntimeError:
        raise HTTPException(status_code=500, detail="All ASR engines failed — could not transcribe")

    if not transcript or len(transcript.strip()) < 2:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    logger.info("[voice/converse] ASR engine=%s, lang=%s, transcript=%s...",
                asr_engine, detected_lang, transcript[:60])

    # Step 2: Fetch body profile for this user (if exists)
    body_profile = None
    try:
        result = await db.execute(
            select(BodyProfile)
            .where(BodyProfile.user_id == user_id)
            .order_by(BodyProfile.created_at.desc())
            .limit(1)
        )
        profile = result.scalar_one_or_none()
        if profile and profile.measurements:
            body_profile = profile.measurements
    except Exception:
        pass  # body profile is optional

    # Load DB history into memory if empty
    await _load_history_if_needed(db, session_id)

    # Step 3: Stylist LLM — negotiate outfit (with detected language) via Agentic Graph
    from services.agent.graph import run_graph
    
    result = await run_graph(
        message=transcript,
        user_id=user_id,
        session_id=session_id,
        language=detected_lang,
        image_b64=None
    )
    
    reply_text = result.get("reply", "") or result.get("error", "Sorry, an error occurred.")
    outfit_state = {
        "intent": result.get("intent"),
        "params": result.get("params"),
        "outfits": result.get("outfits"),
        "status": result.get("status"),
        "error": result.get("error")
    }

    # Note: run_graph already saves the conversation internally via node_memory_save,
    # but we also explicitly add it to the Conversation table for the frontend history.
    try:
        db.add(Conversation(session_id=session_id, role="user", content=transcript, language=detected_lang))
        db.add(Conversation(session_id=session_id, role="assistant", content=reply_text, language=detected_lang))
        await db.commit()
    except Exception as exc:
        logger.warning("[voice/converse] Failed to save conversation: %s", exc)


    # Step 4: TTS — Sarvam Bulbul v3 (primary) → HF MMS (fallback)
    reply_audio_b64 = None
    tts_engine = "none"
    try:
        audio_out, tts_engine = await synthesize_with_fallback(reply_text, language=detected_lang)
        if audio_out and len(audio_out) > 100:
            reply_audio_b64 = base64.b64encode(audio_out).decode("ascii")
            logger.info("[voice/converse] TTS engine=%s, audio_size=%d bytes",
                        tts_engine, len(audio_out))
    except Exception as exc:
        logger.warning("[voice/converse] TTS failed: %s", exc)

    return ConverseResponse(
        transcript=transcript,
        reply_text=reply_text,
        reply_audio_b64=reply_audio_b64,
        detected_language=detected_lang,
        asr_engine=asr_engine,
        tts_engine=tts_engine,
        outfit_state=outfit_state,
    )


class TextConverseRequest(BaseModel):
    """Text-based conversation (for testing / text-chat fallback)."""
    message: str
    session_id: str = "default"
    language: str = "te"


@router.post("/converse-text")
async def voice_converse_text(
    body: TextConverseRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Text-based stylist conversation — also generates TTS audio for the reply."""
    # Isolate session per user
    session_id = f"{user_id}-{body.session_id}"

    # Fetch body profile
    body_profile = None
    try:
        result = await db.execute(
            select(BodyProfile)
            .where(BodyProfile.user_id == user_id)
            .order_by(BodyProfile.created_at.desc())
            .limit(1)
        )
        profile = result.scalar_one_or_none()
        if profile and profile.measurements:
            body_profile = profile.measurements
    except Exception:
        pass

    # Load DB history into memory if empty
    await _load_history_if_needed(db, session_id)

    from services.agent.graph import run_graph
    
    result = await run_graph(
        message=body.message,
        user_id=user_id,
        session_id=session_id,
        language=body.language,
        image_b64=None
    )
    
    reply_text = result.get("reply", "") or result.get("error", "Sorry, an error occurred.")
    outfit_state = {
        "intent": result.get("intent"),
        "params": result.get("params"),
        "outfits": result.get("outfits"),
        "status": result.get("status"),
        "error": result.get("error")
    }

    # Save conversation
    try:
        db.add(Conversation(session_id=session_id, role="user", content=body.message, language=body.language))
        db.add(Conversation(session_id=session_id, role="assistant", content=reply_text, language=body.language))
        await db.commit()
    except Exception as exc:
        logger.warning("[voice/converse-text] Failed to save conversation: %s", exc)


    # Generate TTS for text conversations too (app should speak)
    reply_audio_b64 = None
    tts_engine = "none"
    try:
        audio_out, tts_engine = await synthesize_with_fallback(reply_text, language=body.language)
        if audio_out and len(audio_out) > 100:
            reply_audio_b64 = base64.b64encode(audio_out).decode("ascii")
    except Exception as exc:
        logger.warning("[voice/converse-text] TTS failed: %s", exc)

    return {
        "transcript": body.message,
        "reply_text": reply_text,
        "reply_audio_b64": reply_audio_b64,
        "detected_language": body.language,
        "asr_engine": "text_input",
        "tts_engine": tts_engine,
        "outfit_state": outfit_state,
    }


class FinalizeRequest(BaseModel):
    session_id: str


class FinalizeResponse(BaseModel):
    spec: dict
    image_url: str | None
    outfit_image_b64: str | None = None
    wardrobe_item_id: str | None
    web_matches: list[dict]
    tryon_image_b64: str | None = None
    tailoring: dict | None = None
    reasoning: str | None = None


@router.post("/finalize", response_model=FinalizeResponse)
async def finalize_outfit(
    body: FinalizeRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Finalize outfit: lock spec → generate image → tailoring → web search → try-on via Graph."""
    session_id = f"{user_id}-{body.session_id}"
    from services.agent.graph import run_graph
    
    result = await run_graph(
        message="finalize",
        user_id=user_id,
        session_id=session_id,
        language="en",
        image_b64=None
    )
    
    outfits = result.get("outfits") or []
    outfit_image_b64 = None
    image_url = None
    if outfits:
        outfit_image_b64 = outfits[0].get("image_base64")
        image_url = outfits[0].get("image_url")
        
    if result.get("error"):
        logger.error(f"Finalize Graph Error: {result.get('error')}")
        
    return FinalizeResponse(
        spec=result.get("params", {}),
        image_url=image_url,
        outfit_image_b64=outfit_image_b64,
        wardrobe_item_id=None,
        web_matches=result.get("products") or [],
        tryon_image_b64=result.get("composite_image_b64"),
        tailoring={"pdf_base64": result.get("tailoring_pdf_base64")} if result.get("tailoring_pdf_base64") else None,
        reasoning=None,
    )

@router.get("/converse/history")
async def get_voice_history(
    session_id: str = "default",
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve chat history for a given session."""
    actual_session_id = f"{user_id}-{session_id}"
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == actual_session_id)
        .order_by(Conversation.created_at.asc())
    )
    conversations = result.scalars().all()
    
    history = []
    for conv in conversations:
        history.append({
            "id": conv.id,
            "role": conv.role,
            "content": conv.content,
            "language": conv.language,
            "created_at": conv.created_at.isoformat() if conv.created_at else None
        })
        
    return {"history": history}

