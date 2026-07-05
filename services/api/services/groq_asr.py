"""Groq Whisper ASR — blazing-fast multilingual transcription via Groq Cloud.

Primary ASR engine. Uses the existing GROQ_API_KEY (already on Render).
Whisper Large v3 Turbo handles 99+ languages including Hindi/Telugu/English
code-switching at ~200x realtime on Groq's LPU hardware.
"""

import logging
from io import BytesIO

import httpx

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)

GROQ_ASR_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"

# Map our short codes to Whisper language hints (optional, improves accuracy)
WHISPER_LANG_HINTS = {
    "te": "te",
    "hi": "hi",
    "en": "en",
    "te-IN": "te",
    "hi-IN": "hi",
    "en-IN": "en",
}


async def groq_whisper_asr(
    audio_bytes: bytes,
    language: str | None = None,
) -> tuple[str | None, str | None]:
    """Transcribe audio using Groq Whisper Large v3 Turbo.

    Args:
        audio_bytes: Raw audio bytes (WAV/MP3/WebM/OGG — Whisper accepts all).
        language: Optional language hint (te/hi/en). If None, auto-detects.

    Returns:
        Tuple of (transcript, detected_language) — both None on failure.
    """
    settings = get_settings()
    if not settings.groq_api_key:
        logger.warning("Groq API key not set — skipping Groq Whisper ASR")
        return None, None

    try:
        # Build multipart form data
        files = {"file": ("audio.wav", BytesIO(audio_bytes), "audio/wav")}
        data: dict[str, str] = {
            "model": GROQ_WHISPER_MODEL,
            "response_format": "verbose_json",  # includes detected language
        }

        # Add language hint if provided (improves accuracy)
        if language:
            hint = WHISPER_LANG_HINTS.get(language)
            if hint:
                data["language"] = hint

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                GROQ_ASR_URL,
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                files=files,
                data=data,
            )

            if resp.status_code != 200:
                logger.warning(
                    "Groq Whisper ASR returned %d: %s",
                    resp.status_code,
                    resp.text[:300],
                )
                return None, None

            result = resp.json()
            transcript = result.get("text", "").strip()
            detected_lang = result.get("language", None)

            if transcript:
                logger.info(
                    "Groq Whisper ASR success (detected=%s): %s...",
                    detected_lang,
                    transcript[:80],
                )
                return transcript, detected_lang

            return None, None

    except Exception as exc:
        logger.warning("Groq Whisper ASR failed: %s", exc)
        return None, None
