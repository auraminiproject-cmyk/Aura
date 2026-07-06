"""Virtual try-on via HuggingFace Spaces — free, real compositing.

Uses the Gradio client to call HuggingFace Spaces that host virtual try-on
models. These are completely free to use. Falls back to body-type-aware
SDXL fashion illustration when Spaces are unavailable.

Primary: Kolors Virtual Try-On (Kwai-Kolors) or IDM-VTON
Fallback: SDXL with body-proportioned prompt
"""

import asyncio
import base64
import io
import logging
from typing import Any

import httpx

from services.api.core.config import get_settings
from services.api.core.resilience import hf_breaker

logger = logging.getLogger(__name__)

# HF Spaces that host free virtual try-on models
# We include several low-traffic clones of IDM-VTON to bypass the massive queues on the main spaces
_TRYON_SPACES = [
    "AlexLee01/yisol-IDM-VTON",
    "cocktailpeanut/IDM-VTON",
    "allAI-tools/IDM-VTON",
    "yisol/IDM-VTON",
    "Kwai-Kolors/Kolors-Virtual-Try-On",
]


async def try_on_with_spaces(
    person_image_bytes: bytes,
    garment_image_bytes: bytes,
) -> bytes | None:
    """Call a HuggingFace Space for virtual try-on.

    Uses the Gradio client to call free Spaces. Returns composited image bytes.
    """
    try:
        from gradio_client import Client, handle_file  # type: ignore[import-untyped]
        import tempfile
        import os

        loop = asyncio.get_event_loop()

        def _call_space():
            # Write images to temp files (Gradio client needs file paths)
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f_person:
                f_person.write(person_image_bytes)
                person_path = f_person.name
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f_garment:
                f_garment.write(garment_image_bytes)
                garment_path = f_garment.name

            try:
                # Try each Space until one works
                for space_id in _TRYON_SPACES:
                    try:
                        client = Client(space_id)
                        result = client.predict(
                            handle_file(person_path),
                            handle_file(garment_path),
                            api_name="/tryon",
                        )
                        # Result is typically a file path or tuple
                        if isinstance(result, str) and os.path.exists(result):
                            with open(result, "rb") as f:
                                return f.read()
                        if isinstance(result, (list, tuple)):
                            for item in result:
                                if isinstance(item, str) and os.path.exists(item):
                                    with open(item, "rb") as f:
                                        return f.read()
                        logger.info("Try-on Space %s returned unexpected type: %s", space_id, type(result))
                    except Exception as exc:
                        logger.warning("Space %s failed: %s", space_id, exc)
                        continue
            finally:
                try:
                    os.unlink(person_path)
                except OSError:
                    pass
                try:
                    os.unlink(garment_path)
                except OSError:
                    pass
            return None

        result = await asyncio.wait_for(
            loop.run_in_executor(None, _call_space),
            timeout=120.0,  # Spaces can be slow on cold start
        )
        return result

    except ImportError:
        logger.warning("gradio_client not installed — pip install gradio_client")
        return None
    except asyncio.TimeoutError:
        logger.warning("Try-on Space call timed out")
        return None
    except Exception as exc:
        logger.warning("Try-on Spaces failed: %s", exc)
        return None


async def generate_tryon_image(
    *,
    spec: dict[str, Any],
    person_image_bytes: bytes | None = None,
    garment_image_bytes: bytes | None = None,
    body_analysis: dict[str, Any] | None = None,
) -> tuple[bytes | None, str]:
    """Generate a virtual try-on image.

    Strategy:
    1. If we have both person image + garment image → use HF Space for real compositing
    2. Otherwise → generate body-type-aware SDXL illustration

    Returns:
        Tuple of (image_bytes, engine_used).
    """
    # Strategy 1: Real virtual try-on if we have both images
    if person_image_bytes and garment_image_bytes:
        logger.info("[tryon] Attempting real virtual try-on with HF Spaces")
        result = await try_on_with_spaces(person_image_bytes, garment_image_bytes)
        if result and len(result) > 500:
            logger.info("[tryon] Real virtual try-on succeeded (%d bytes)", len(result))
            return result, "hf-space-vton"

    # Strategy 2: Body-type-aware SDXL illustration
    logger.info("[tryon] Generating body-type-aware SDXL illustration")
    result = await _sdxl_body_illustration(spec, body_analysis)
    if result and len(result) > 500:
        return result, "sdxl-body-illustration"

    return None, "none"


async def _sdxl_body_illustration(
    spec: dict[str, Any],
    body_analysis: dict[str, Any] | None = None,
) -> bytes | None:
    """Generate body-type-aware fashion illustration via HF SDXL.

    This isn't a true composite — it's a high-quality fashion illustration
    that reflects the user's body type and the designed outfit.
    """
    settings = get_settings()
    if not settings.huggingface_api_key:
        return None

    # Build body-aware prompt
    body_desc = ""
    if body_analysis:
        body_type = body_analysis.get("body_type", "")
        height_cat = body_analysis.get("height_category", "average")
        body_type_prompts = {
            "hourglass": "woman with defined waist, balanced proportions",
            "pear": "woman with narrow shoulders and wider hips",
            "apple": "woman with fuller midsection, balanced shoulders",
            "rectangle": "woman with athletic straight frame",
            "inverted_triangle": "woman with broad shoulders and narrow hips",
        }
        height_prompts = {
            "petite": "petite",
            "tall": "tall",
            "average": "average height",
        }
        body_desc = f"{height_prompts.get(height_cat, '')} {body_type_prompts.get(body_type, 'woman')}"

    garment = spec.get("garment_type", "outfit")
    fabric = spec.get("fabric", "silk")
    color = spec.get("color", "red")
    silhouette = spec.get("silhouette", "")
    style_notes = spec.get("style_notes", "")

    prompt_parts = [
        f"Fashion editorial photo of {body_desc}" if body_desc else "Fashion editorial photo",
        f"wearing {color} {fabric} {garment}",
        f"{silhouette} silhouette" if silhouette else "",
        style_notes,
        "Indian fashion, studio lighting, full body shot",
        "detailed fabric texture, professional fashion photography, 4k quality",
        "realistic body proportions, natural pose",
    ]
    prompt = ", ".join(p for p in prompt_parts if p)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization": f"Bearer {settings.huggingface_api_key}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "num_inference_steps": 30,
                        "guidance_scale": 7.5,
                        "width": 512,
                        "height": 768,
                    },
                },
            )
            if resp.status_code == 200 and len(resp.content) > 500:
                hf_breaker.success()
                return resp.content
            if resp.status_code in (503, 429):
                hf_breaker.fail()
            logger.warning("SDXL illustration returned %d", resp.status_code)
    except Exception as exc:
        logger.warning("SDXL illustration failed: %s", exc)

    return None
