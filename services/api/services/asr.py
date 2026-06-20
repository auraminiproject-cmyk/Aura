import base64
import io
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)


def _to_16k_mono_wav(audio_bytes: bytes) -> bytes:
    """Normalize input to 16kHz mono WAV for Whisper."""
    try:
        import io

        import numpy as np
        import soundfile as sf

        data, samplerate = sf.read(io.BytesIO(audio_bytes))
        if data.ndim > 1:
            data = data.mean(axis=1)
        if samplerate != 16000:
            duration = len(data) / samplerate
            new_len = int(duration * 16000)
            data = np.interp(
                np.linspace(0, len(data) - 1, new_len),
                np.arange(len(data)),
                data,
            )
        buf = io.BytesIO()
        sf.write(buf, data, 16000, format="WAV")
        return buf.getvalue()
    except Exception:
        return audio_bytes


@retry(wait=wait_exponential(multiplier=1, min=1, max=6), stop=stop_after_attempt(2), reraise=True)
async def transcribe_audio(audio_bytes: bytes, language: str | None = None) -> str:
    settings = get_settings()
    audio_bytes = _to_16k_mono_wav(audio_bytes)
    if settings.huggingface_api_key:
        try:
            return await _hf_whisper(audio_bytes, language)
        except httpx.HTTPError as exc:
            logger.warning("HF Whisper failed: %s", exc)

    return _mock_transcribe(audio_bytes)


async def _hf_whisper(audio_bytes: bytes, language: str | None) -> str:
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
    params = {}
    if language:
        params["language"] = language

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api-inference.huggingface.co/models/openai/whisper-large-v3",
            headers=headers,
            files=files,
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "text" in data:
            return data["text"].strip()
        if isinstance(data, list) and data and "text" in data[0]:
            return data[0]["text"].strip()
        return str(data)


def _mock_transcribe(_audio_bytes: bytes) -> str:
    return "Namaste, naaku wedding ki red lehenga kavali, budget 5000 rupees."
