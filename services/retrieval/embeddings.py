"""FashionCLIP / text embeddings for hybrid retrieval."""

import hashlib
import logging

import httpx

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)
VECTOR_DIM = 512


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.huggingface_api_key:
        try:
            return _hf_embed(text, settings)
        except Exception as exc:
            logger.warning("HF embed failed: %s", exc)
    return _pseudo_embed(text)


def _pseudo_embed(text: str, dim: int = VECTOR_DIM) -> list[float]:
    h = hashlib.sha512(text.encode()).digest()
    vals = [((h[i % len(h)] / 255.0) * 2 - 1) for i in range(dim)]
    norm = sum(v * v for v in vals) ** 0.5 or 1.0
    return [v / norm for v in vals]


def _hf_embed(text: str, settings) -> list[float]:
    model = settings.fashionclip_model
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}",
            headers={"Authorization": f"Bearer {settings.huggingface_api_key}"},
            json={"inputs": text},
        )
        if resp.status_code == 200:
            vec = resp.json()
            if isinstance(vec, list) and vec and isinstance(vec[0], (int, float)):
                flat = vec  # type: ignore
            elif isinstance(vec, list) and vec and isinstance(vec[0], list):
                flat = vec[0]
            else:
                flat = _pseudo_embed(text)
            if len(flat) != VECTOR_DIM:
                return _pseudo_embed(text)
            norm = sum(x * x for x in flat) ** 0.5 or 1.0
            return [x / norm for x in flat]
    return _pseudo_embed(text)
