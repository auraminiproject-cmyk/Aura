"""Virtual try-on — Kolors VTON via HF Spaces → simple composite fallback.

Production: Calls Kolors Virtual Try-On on Hugging Face Spaces via Gradio API.
Fallback: Returns a blended composite of outfit + user photo.
"""

import base64
import logging
from io import BytesIO

import httpx

from services.api.core.config import get_settings
from services.api.core.resilience import hf_breaker

logger = logging.getLogger(__name__)

# HF Spaces API for Kolors VTON (free tier)
KOLORS_VTON_SPACE = "Kwai-Kolors/Kolors-Virtual-Try-On"


async def virtual_tryon(*, outfit_image_b64: str, user_photo_b64: str) -> dict:
    """Virtual try-on: composite outfit onto user photo.

    Chain: Kolors VTON (HF Spaces) → simple blend fallback.
    """
    settings = get_settings()

    # Tier 1: Kolors VTON via HF Spaces Gradio API
    if settings.huggingface_api_key and hf_breaker.current_state != "open":
        try:
            result_b64 = await _kolors_tryon(outfit_image_b64, user_photo_b64, settings)
            if result_b64:
                return {
                    "result_image_base64": result_b64,
                    "quality_score": 0.85,
                    "provider": "kolors-vton",
                }
        except Exception as exc:
            logger.warning("Kolors VTON failed: %s", exc)

    # Tier 2: Simple blend composite
    try:
        result_b64 = _blend_composite(outfit_image_b64, user_photo_b64)
        return {
            "result_image_base64": result_b64,
            "quality_score": 0.55,
            "provider": "blend-fallback",
        }
    except Exception as exc:
        logger.warning("Blend fallback failed: %s", exc)

    # Tier 3: Return outfit image as-is
    return {
        "result_image_base64": outfit_image_b64,
        "quality_score": 0.3,
        "provider": "passthrough",
    }


async def _kolors_tryon(outfit_b64: str, user_b64: str, settings) -> str | None:
    """Call Kolors VTON via HF Spaces Gradio API."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        # HF Spaces Gradio API endpoint
        resp = await client.post(
            f"https://{KOLORS_VTON_SPACE.replace('/', '-').lower()}.hf.space/api/predict",
            json={
                "data": [
                    f"data:image/png;base64,{user_b64}",
                    f"data:image/png;base64,{outfit_b64}",
                ],
            },
        )
        if resp.status_code == 503:
            hf_breaker.fail()
            logger.info("Kolors VTON Space loading (cold start)")
            return None
        if resp.status_code != 200:
            logger.warning("Kolors VTON returned %d", resp.status_code)
            return None

        hf_breaker.success()
        data = resp.json()
        # Gradio returns {"data": ["data:image/png;base64,..."]}
        if "data" in data and data["data"]:
            result = data["data"][0]
            if isinstance(result, str) and "base64," in result:
                return result.split("base64,", 1)[1]
            if isinstance(result, dict) and "url" in result:
                # Download the result image
                img_resp = await client.get(result["url"])
                if img_resp.status_code == 200:
                    return base64.b64encode(img_resp.content).decode("ascii")
        return None


def _blend_composite(outfit_b64: str, user_b64: str) -> str:
    """Simple alpha-blend composite of outfit onto user photo."""
    from PIL import Image

    outfit_bytes = base64.b64decode(outfit_b64)
    user_bytes = base64.b64decode(user_b64)

    user_img = Image.open(BytesIO(user_bytes)).convert("RGBA")
    outfit_img = Image.open(BytesIO(outfit_bytes)).convert("RGBA")

    # Resize outfit to match user image dimensions
    outfit_img = outfit_img.resize(user_img.size, Image.LANCZOS)

    # Alpha blend: 60% user + 40% outfit
    blended = Image.blend(user_img, outfit_img, alpha=0.4)

    buf = BytesIO()
    blended.convert("RGB").save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")
