"""Vision-Language Model integration — Qwen2.5-VL via Groq Vision / HF Inference.

Supports:
  - Clothing analysis from photos (describe garment, detect style/color/pattern)
  - Outfit evaluation and improvement suggestions
  - Body-type aware styling recommendations

Routing: Groq Vision (llama-3.2-90b-vision) → HF Inference (Qwen2.5-VL) → text-only fallback.
"""

import base64
import logging
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.api.core.config import get_settings
from services.api.core.resilience import groq_breaker, hf_breaker

logger = logging.getLogger(__name__)


@dataclass
class VLMResult:
    description: str
    tags: list[str]
    style_category: str
    color_palette: list[str]
    suggestions: list[str]
    provider: str
    confidence: float


VLM_SYSTEM_PROMPT = """You are AURA, an expert AI fashion stylist specializing in Indian and global fashion.
Analyze the provided clothing/outfit image and return a structured analysis.

Your response MUST follow this exact format:
DESCRIPTION: [2-3 sentence description of the garment/outfit]
TAGS: [comma-separated tags: e.g., ethnic, wedding, silk, embroidered, formal]
STYLE: [one of: Traditional Indian, Indo-Western, Western Casual, Western Formal, Streetwear, Athleisure, Ethnic Festive, Bridal]
COLORS: [comma-separated dominant colors]
SUGGESTIONS: [2-3 styling suggestions, semicolon-separated]
CONFIDENCE: [0.0-1.0 confidence score]"""

OUTFIT_EVAL_PROMPT = """You are AURA, an expert AI fashion stylist. Evaluate this outfit image.
Consider: body type compatibility, occasion appropriateness, color harmony, fabric quality, and cultural context.

Your response MUST follow this exact format:
SCORE: [1-10 overall score]
STRENGTHS: [2-3 strengths, semicolon-separated]
IMPROVEMENTS: [2-3 improvement suggestions, semicolon-separated]
OCCASIONS: [comma-separated suitable occasions]
BODY_TYPES: [comma-separated body types this would flatter]"""


@retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(2), reraise=True)
async def analyze_clothing_image(
    image_bytes: bytes,
    *,
    prompt: str | None = None,
    language: str = "en",
) -> VLMResult:
    """Analyze a clothing/outfit image using VLM.

    Tries: Groq Vision → HF Qwen2.5-VL → text-only heuristic fallback.
    """
    settings = get_settings()
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    user_prompt = prompt or "Analyze this clothing item in detail."

    if language == "te":
        user_prompt += " Respond with Telugu transliteration where possible."
    elif language == "hi":
        user_prompt += " Respond in Hindi where possible."

    # Tier 1: Groq Vision (llama-3.2-90b-vision-preview or similar)
    if settings.groq_api_key and groq_breaker.current_state != "open":
        try:
            text = await _groq_vision(image_b64, user_prompt, settings)
            return _parse_vlm_response(text, provider="groq-vision")
        except Exception as exc:
            logger.warning("Groq Vision failed: %s", exc)

    # Tier 2: HF Inference API (Qwen2.5-VL)
    if settings.huggingface_api_key and hf_breaker.current_state != "open":
        try:
            text = await _hf_vlm(image_b64, user_prompt, settings)
            return _parse_vlm_response(text, provider="hf-qwen2.5-vl")
        except Exception as exc:
            logger.warning("HF VLM failed: %s", exc)

    # Tier 3: Text-only fallback (no vision)
    return _heuristic_fallback(user_prompt)


async def evaluate_outfit_image(
    image_bytes: bytes,
    *,
    context: str = "",
) -> dict:
    """Evaluate an outfit image and provide scoring + suggestions."""
    settings = get_settings()
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    eval_prompt = f"Evaluate this outfit. Context: {context}" if context else "Evaluate this outfit."

    # Try Groq Vision first
    if settings.groq_api_key and groq_breaker.current_state != "open":
        try:
            text = await _groq_vision(image_b64, eval_prompt, settings, system=OUTFIT_EVAL_PROMPT)
            return _parse_eval_response(text)
        except Exception as exc:
            logger.warning("Groq Vision eval failed: %s", exc)

    # Try HF
    if settings.huggingface_api_key and hf_breaker.current_state != "open":
        try:
            text = await _hf_vlm(image_b64, eval_prompt, settings)
            return _parse_eval_response(text)
        except Exception as exc:
            logger.warning("HF VLM eval failed: %s", exc)

    return {
        "score": 7,
        "strengths": ["Good color coordination", "Appropriate for occasion"],
        "improvements": ["Consider accessorizing", "Try layering for depth"],
        "occasions": ["casual", "semi-formal"],
        "body_types": ["all"],
        "provider": "fallback",
    }


# ── Providers ────────────────────────────────────────────────────────────────


async def _groq_vision(
    image_b64: str, prompt: str, settings, *, system: str | None = None,
) -> str:
    """Send image + text to Groq's vision-capable model."""
    sys_prompt = system or VLM_SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": sys_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                },
            ],
        },
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": "llama-3.2-90b-vision-preview",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1024,
            },
        )
        if resp.status_code == 429:
            groq_breaker.fail()
            raise RuntimeError("Groq rate limited")
        resp.raise_for_status()
        data = resp.json()
        groq_breaker.success()
        return data["choices"][0]["message"]["content"].strip()


async def _hf_vlm(image_b64: str, prompt: str, settings) -> str:
    """Send image + text to HF Inference API for Qwen2.5-VL."""
    async with httpx.AsyncClient(timeout=90.0) as client:
        # HF Inference API supports vision models via messages format
        resp = await client.post(
            "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-VL-7B-Instruct",
            headers={"Authorization": f"Bearer {settings.huggingface_api_key}"},
            json={
                "inputs": {
                    "image": image_b64,
                    "text": f"{VLM_SYSTEM_PROMPT}\n\n{prompt}",
                },
            },
        )
        if resp.status_code == 503:
            hf_breaker.fail()
            raise RuntimeError("HF model loading (cold start)")
        resp.raise_for_status()
        data = resp.json()
        hf_breaker.success()
        if isinstance(data, list) and data:
            return data[0].get("generated_text", str(data))
        if isinstance(data, dict):
            return data.get("generated_text", str(data))
        return str(data)


# ── Parsers ──────────────────────────────────────────────────────────────────


def _parse_vlm_response(text: str, *, provider: str) -> VLMResult:
    """Parse structured VLM response into VLMResult."""
    lines = text.strip().split("\n")
    fields: dict[str, str] = {}
    for line in lines:
        for key in ("DESCRIPTION", "TAGS", "STYLE", "COLORS", "SUGGESTIONS", "CONFIDENCE"):
            if line.upper().startswith(f"{key}:"):
                fields[key.lower()] = line.split(":", 1)[1].strip()

    tags = [t.strip() for t in fields.get("tags", "fashion").split(",") if t.strip()]
    colors = [c.strip() for c in fields.get("colors", "").split(",") if c.strip()]
    suggestions = [s.strip() for s in fields.get("suggestions", "").split(";") if s.strip()]

    try:
        confidence = float(fields.get("confidence", "0.75"))
    except ValueError:
        confidence = 0.75

    return VLMResult(
        description=fields.get("description", text[:200]),
        tags=tags or ["fashion"],
        style_category=fields.get("style", "Unknown"),
        color_palette=colors or ["unknown"],
        suggestions=suggestions or ["No specific suggestions"],
        provider=provider,
        confidence=min(max(confidence, 0.0), 1.0),
    )


def _parse_eval_response(text: str) -> dict:
    """Parse outfit evaluation response."""
    lines = text.strip().split("\n")
    fields: dict[str, str] = {}
    for line in lines:
        for key in ("SCORE", "STRENGTHS", "IMPROVEMENTS", "OCCASIONS", "BODY_TYPES"):
            if line.upper().startswith(f"{key}:"):
                fields[key.lower()] = line.split(":", 1)[1].strip()

    try:
        score = int(fields.get("score", "7"))
    except ValueError:
        score = 7

    return {
        "score": min(max(score, 1), 10),
        "strengths": [s.strip() for s in fields.get("strengths", "").split(";") if s.strip()],
        "improvements": [s.strip() for s in fields.get("improvements", "").split(";") if s.strip()],
        "occasions": [o.strip() for o in fields.get("occasions", "").split(",") if o.strip()],
        "body_types": [b.strip() for b in fields.get("body_types", "all").split(",") if b.strip()],
        "provider": "vlm",
    }


def _heuristic_fallback(prompt: str) -> VLMResult:
    """Text-only fallback when no VLM provider is available."""
    lower = prompt.lower()
    if any(w in lower for w in ("saree", "sari", "silk")):
        return VLMResult(
            description="Traditional Indian saree — elegant drape suitable for festive and formal occasions.",
            tags=["ethnic", "saree", "traditional", "Indian"],
            style_category="Traditional Indian",
            color_palette=["varies"],
            suggestions=["Pair with statement jewelry", "Choose contrast blouse", "Add waist belt for modern twist"],
            provider="fallback",
            confidence=0.4,
        )
    if any(w in lower for w in ("lehenga", "choli")):
        return VLMResult(
            description="Indian lehenga choli — festive and bridal ensemble with rich embroidery.",
            tags=["ethnic", "lehenga", "bridal", "festive"],
            style_category="Ethnic Festive",
            color_palette=["red", "gold"],
            suggestions=["Match dupatta shade", "Go for minimal jewelry if heavy embroidery"],
            provider="fallback",
            confidence=0.4,
        )
    return VLMResult(
        description="Fashion item detected. Upload a clearer image for detailed AI analysis.",
        tags=["fashion"],
        style_category="Unknown",
        color_palette=["unknown"],
        suggestions=["Upload a well-lit photo", "Include full garment in frame", "Try front and side views"],
        provider="fallback",
        confidence=0.3,
    )
