"""Sarvam AI client — ASR (Saaras v3) + TTS (Bulbul v3) for Indic voice.

Primary TTS engine for Telugu/Hindi/English code-mixed speech.
ASR is secondary (Groq Whisper is primary for ASR).
Falls back to HF Whisper ASR / HF MMS TTS when both Groq and Sarvam are unavailable.
"""

import base64
import logging
from io import BytesIO

import httpx

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)

SARVAM_BASE = "https://api.sarvam.ai"

# Language code mapping for Sarvam API
SARVAM_LANG_MAP = {
    "te": "te-IN",
    "hi": "hi-IN",
    "en": "en-IN",
    "te-IN": "te-IN",
    "hi-IN": "hi-IN",
    "en-IN": "en-IN",
    # Whisper returns full language names — map those too
    "telugu": "te-IN",
    "hindi": "hi-IN",
    "english": "en-IN",
}

# TTS speaker voices available in Sarvam Bulbul
# Valid speakers: anushka, abhilash, manisha, vidya, arya, karun, hitesh, aditya, ritu, priya, neha, rahul, pooja, rohan, simran, kavya
SARVAM_SPEAKERS = {
    "te": "anushka",
    "hi": "anushka",
    "en": "anushka",
    "te-IN": "anushka",
    "hi-IN": "anushka",
    "en-IN": "anushka",
    "telugu": "anushka",
    "hindi": "anushka",
    "english": "anushka",
}

# Map Whisper's detected language to our short codes
WHISPER_LANG_TO_SHORT = {
    "telugu": "te",
    "hindi": "hi",
    "english": "en",
    "te": "te",
    "hi": "hi",
    "en": "en",
    "te-in": "te",
    "hi-in": "hi",
    "en-in": "en",
}


def normalize_language(lang: str | None) -> str:
    """Normalize any language identifier to our short code (te/hi/en)."""
    if not lang:
        return "hi"  # default to Hindi
    lang_lower = lang.lower().strip()
    return WHISPER_LANG_TO_SHORT.get(lang_lower, "hi")


async def sarvam_asr(audio_bytes: bytes, language: str = "te") -> tuple[str | None, str | None]:
    """Transcribe audio using Sarvam Saaras v3 ASR.

    Args:
        audio_bytes: Raw audio bytes (WAV/MP3/WebM).
        language: Language code (te/hi/en or te-IN/hi-IN/en-IN).

    Returns:
        Tuple of (transcript, detected_language_short) — both None on failure.
    """
    settings = get_settings()
    if not settings.sarvam_api_key:
        return None, None

    lang_code = SARVAM_LANG_MAP.get(language, "hi-IN")

    try:
        # Sarvam ASR expects base64 audio in JSON body
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{SARVAM_BASE}/speech-to-text",
                headers={
                    "api-subscription-key": settings.sarvam_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "input": audio_b64,
                    "language_code": lang_code,
                    "model": "saaras:v3",
                    "with_timestamps": False,
                },
            )
            if resp.status_code != 200:
                logger.warning("Sarvam ASR returned %d: %s", resp.status_code, resp.text[:200])
                return None, None

            data = resp.json()
            transcript = data.get("transcript", "")
            detected = normalize_language(language)
            if transcript:
                logger.info("[ASR:sarvam] success (%s): %s...", lang_code, transcript[:60])
                return transcript, detected
            return None, None

    except Exception as exc:
        logger.warning("Sarvam ASR failed: %s", exc)
        return None, None


async def sarvam_tts(text: str, language: str = "te") -> bytes | None:
    """Synthesize speech using Sarvam Bulbul v3 TTS.

    Args:
        text: Text to synthesize (max ~2500 chars for v3).
        language: Target language code.

    Returns:
        Audio bytes (WAV), or None on failure.
    """
    settings = get_settings()
    if not settings.sarvam_api_key:
        return None

    lang_code = SARVAM_LANG_MAP.get(language, "hi-IN")
    speaker = SARVAM_SPEAKERS.get(language, "anushka")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{SARVAM_BASE}/text-to-speech",
                headers={
                    "api-subscription-key": settings.sarvam_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": [text[:2500]],
                    "target_language_code": lang_code,
                    "speaker": speaker,
                    "model": "bulbul:v2",
                    "enable_preprocessing": True,
                },
            )
            if resp.status_code != 200:
                logger.warning("Sarvam TTS returned %d: %s", resp.status_code, resp.text[:200])
                return None

            data = resp.json()
            # Sarvam returns base64-encoded audio in "audios" array
            audios = data.get("audios")
            if audios and len(audios) > 0:
                audio_b64 = audios[0]
                audio_bytes = base64.b64decode(audio_b64)
                logger.info("[TTS:sarvam] success (%s), %d bytes", lang_code, len(audio_bytes))
                return audio_bytes
            return None

    except Exception as exc:
        logger.warning("Sarvam TTS failed: %s", exc)
        return None


async def transcribe_with_fallback(
    audio_bytes: bytes,
    language: str | None = None,
) -> tuple[str, str, str]:
    """Transcribe audio: Groq Whisper → Sarvam → HF Whisper (NO mock fallback).

    Returns:
        Tuple of (transcript, detected_language_short, engine_used).
        Raises HTTPException if all engines fail.
    """
    # Tier 1: Groq Whisper (primary — uses existing GROQ_API_KEY)
    from services.api.services.groq_asr import groq_whisper_asr

    transcript, detected = await groq_whisper_asr(audio_bytes, language)
    if transcript:
        lang_short = normalize_language(detected)
        return transcript, lang_short, "groq_whisper"

    # Tier 2: Sarvam Saaras v3
    lang_hint = language or "hi"
    transcript, detected = await sarvam_asr(audio_bytes, lang_hint)
    if transcript:
        return transcript, detected or normalize_language(lang_hint), "sarvam_saaras"

    # Tier 3: HF Whisper (genuine last resort — no mock)
    from services.api.services.asr import transcribe_audio

    transcript = await transcribe_audio(audio_bytes, language=language)
    if transcript and transcript.strip():
        return transcript, normalize_language(language), "hf_whisper"

    # All failed — explicit failure, never a mock
    raise RuntimeError("All ASR engines failed — no transcript available")


async def synthesize_with_fallback(
    text: str,
    language: str = "te",
) -> tuple[bytes | None, str]:
    """Synthesize speech: Sarvam Bulbul v3 → HF MMS TTS (NO silent placeholder).

    Returns:
        Tuple of (audio_bytes, engine_used). audio_bytes may be None if all fail.
    """
    # Tier 1: Sarvam Bulbul v3 (primary)
    audio = await sarvam_tts(text, language)
    if audio:
        return audio, "sarvam_bulbul"

    # Tier 2: HF MMS TTS (genuine fallback)
    from services.api.services.tts import synthesize_speech

    result_b64 = await synthesize_speech(text, language=language)
    if result_b64:
        return base64.b64decode(result_b64), "hf_mms_tts"

    # All failed — log explicitly, return None (caller must handle)
    logger.error("[TTS] All engines failed for lang=%s, text_len=%d", language, len(text))
    return None, "none"
