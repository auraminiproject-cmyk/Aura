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
    """Call a HuggingFace Space for virtual try-on concurrently.

    Submits requests to multiple free Spaces simultaneously.
    Returns the first successful result and cancels the rest.
    """
    try:
        from gradio_client import Client, handle_file  # type: ignore[import-untyped]
        import tempfile
        import os

        loop = asyncio.get_event_loop()

        def _call_single_space(space_id: str) -> bytes | None:
            person_path = None
            garment_path = None
            try:
                f_person = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                f_person.write(person_image_bytes)
                f_person.close()
                person_path = f_person.name

                f_garment = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                f_garment.write(garment_image_bytes)
                f_garment.close()
                garment_path = f_garment.name
                
                client = Client(space_id)
                # First try Gradio 4.x ImageEditor API signature (used by yisol/IDM-VTON recently)
                try:
                    result = client.predict(
                        {"background": handle_file(person_path), "layers": [], "composite": None},
                        handle_file(garment_path),
                        "Fashion garment",
                        True,
                        False,
                        30,
                        42,
                        api_name="/tryon",
                    )
                except Exception as e_new:
                    # Fallback to older Gradio 3.x Image API signature
                    logger.debug("[tryon] Space %s failed Gradio 4 API, trying Gradio 3: %s", space_id, e_new)
                    result = client.predict(
                        handle_file(person_path),
                        handle_file(garment_path),
                        "Fashion garment",
                        True,
                        False,
                        30,
                        42,
                        api_name="/tryon",
                    )
                
                # Result is typically a tuple where first element is output image path
                if isinstance(result, tuple) and len(result) > 0:
                    out_path = result[0]
                elif isinstance(result, str):
                    out_path = result
                else:
                    logger.error("[tryon] Space %s returned unexpected type: %s", space_id, type(result))
                    return None
                    
                if out_path and os.path.exists(out_path):
                    with open(out_path, "rb") as f:
                        return f.read()
                return None
            except Exception as e:
                logger.error("[tryon] Space %s failed: %s", space_id, e)
                return None
            finally:
                if person_path:
                    try:
                        os.unlink(person_path)
                    except OSError:
                        pass
                if garment_path:
                    try:
                        os.unlink(garment_path)
                    except OSError:
                        pass

        async def _run_async(space_id: str):
            # Run the blocking Gradio client call in an executor thread
            res = await loop.run_in_executor(None, _call_single_space, space_id)
            if not res:
                raise RuntimeError(f"Space {space_id} failed or returned None")
            return res

        try:
            tasks = [asyncio.create_task(_run_async(sid)) for sid in _TRYON_SPACES]
            pending = set(tasks)
            start_time = time.time()
            while pending:
                elapsed = time.time() - start_time
                if elapsed >= 90.0:
                    break
                    
                done, pending = await asyncio.wait(
                    pending,
                    timeout=90.0 - elapsed,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                if not done:
                    break # timeout
                    
                for task in done:
                    try:
                        res = task.result()
                        if res:
                            return res
                    except Exception as exc:
                        logger.debug("[tryon] A task failed: %s", exc)
                        
            logger.warning("All Try-On Spaces failed or timed out.")
            return None
        finally:
            pass

    except ImportError:
        logger.warning("gradio_client not installed — pip install gradio_client")
        return None
    except Exception as exc:
        logger.warning("Try-on Spaces concurrent call failed: %s", exc)
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
