"""TTS — Kokoro local → HF Inference API → silent WAV placeholder.

On Render (no GPU, 512MB RAM) Kokoro may not fit, so we fall through
to HF Inference API for real speech synthesis.
"""

import base64
import logging
import struct
import wave
from io import BytesIO

import httpx

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)


async def synthesize_speech(text: str, *, language: str = "te") -> str | None:
    """Synthesize speech; returns base64 WAV.

    Chain: Kokoro local → HF Inference API → silent WAV placeholder.
    """
    # Tier 1: Kokoro local (CPU, 50x realtime)
    try:
        result = _kokoro_local(text, language)
        if result:
            return result
    except Exception as exc:
        logger.debug("Kokoro local unavailable: %s", exc)

    # Tier 2: HF Inference API (free tier)
    try:
        result = await _hf_tts(text, language)
        if result:
            return result
    except Exception as exc:
        logger.warning("HF TTS failed: %s", exc)

    # Tier 3: Silent WAV placeholder
    logger.debug("All TTS providers unavailable; returning silent WAV")
    return _silent_wav_base64(duration_ms=min(len(text) * 40, 8000))


def _kokoro_local(text: str, language: str) -> str | None:
    """Try Kokoro-82M local inference."""
    try:
        from kokoro import KPipeline  # type: ignore

        pipeline = KPipeline(lang_code=_lang_code(language))
        audio_chunks = []
        for _, _, audio in pipeline(text):
            audio_chunks.append(audio)
        if not audio_chunks:
            return None
        import numpy as np

        combined = np.concatenate(audio_chunks)
        buf = BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes((combined * 32767).astype("int16").tobytes())
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except ImportError:
        return None


async def _hf_tts(text: str, language: str) -> str | None:
    """Use HF Inference API for TTS (facebook/mms-tts or espnet)."""
    settings = get_settings()
    if not settings.huggingface_api_key:
        return None

    # Map language to HF TTS model
    model_map = {
        "te": "facebook/mms-tts-tel",
        "hi": "facebook/mms-tts-hin",
        "en": "facebook/mms-tts-eng",
    }
    model = model_map.get(language, "facebook/mms-tts-eng")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {settings.huggingface_api_key}"},
            json={"inputs": text[:500]},  # Limit text length for free tier
        )
        if resp.status_code == 503:
            logger.info("HF TTS model loading (cold start)")
            return None
        if resp.status_code != 200:
            logger.warning("HF TTS returned %d", resp.status_code)
            return None
        # HF returns raw audio bytes (flac/wav)
        audio_bytes = resp.content
        if len(audio_bytes) < 100:
            return None
        return base64.b64encode(audio_bytes).decode("ascii")


def _lang_code(language: str) -> str:
    return {"te": "te", "hi": "h", "en": "a"}.get(language, "a")


def _silent_wav_base64(duration_ms: int = 500) -> str:
    rate = 24000
    nframes = int(rate * duration_ms / 1000)
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack("<" + "h" * nframes, *([0] * nframes)))
    return base64.b64encode(buf.getvalue()).decode("ascii")
