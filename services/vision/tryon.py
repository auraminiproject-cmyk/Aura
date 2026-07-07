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
    """Call IDM-VTON via HF Spaces Gradio Client."""
    import asyncio
    import os
    import tempfile
    
    def run_vton():
        try:
            from gradio_client import Client, handle_file
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_user:
                f_user.write(base64.b64decode(user_b64))
                user_path = f_user.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_outfit:
                f_outfit.write(base64.b64decode(outfit_b64))
                outfit_path = f_outfit.name
                
            client = Client("yisol/IDM-VTON")
            result = client.predict(
                dict={"background": handle_file(user_path), "layers": [], "composite": None},
                garm_img=handle_file(outfit_path),
                garment_des="fashion outfit",
                is_checked=True,
                is_checked_crop=False,
                denoise_steps=20,
                seed=42,
                api_name="/tryon"
            )
            res_path = result[0]
            with open(res_path, "rb") as f:
                res_b64 = base64.b64encode(f.read()).decode("ascii")
                
            os.remove(user_path)
            os.remove(outfit_path)
            return res_b64
        except ImportError:
            logger.warning("gradio_client not installed, skipping VTON")
            return None
        except Exception as e:
            logger.warning(f"IDM-VTON failed: {e}")
            if 'user_path' in locals() and os.path.exists(user_path):
                os.remove(user_path)
            if 'outfit_path' in locals() and os.path.exists(outfit_path):
                os.remove(outfit_path)
            return None

    return await asyncio.to_thread(run_vton)


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
