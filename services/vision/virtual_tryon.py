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
    prompt: str = "Fashion garment",
) -> bytes | None:
    """Call a HuggingFace Space for virtual try-on concurrently with retries.

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
                        prompt,
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
                        prompt,
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

        for attempt in range(2):
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
                            
                logger.warning("Attempt %d: All Try-On Spaces failed or timed out.", attempt + 1)
            except Exception as e:
                logger.warning("Attempt %d: Retry loop error: %s", attempt + 1, e)
        
        return None
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
    Strictly use HF Space for real compositing if both images are present.
    NEVER fall back to SDXL (random models).

    Returns:
        Tuple of (image_bytes, engine_used).
    """
    if not person_image_bytes:
        raise ValueError("avatar_missing")
        
    if not garment_image_bytes:
        raise ValueError("garment_missing")

    # Construct the strict prompt as per user requirements
    _garment = spec.get("garment_type", "outfit")
    _fabric = spec.get("fabric", "")
    _color = spec.get("color", "")
    outfit_desc = f"{_color} {_fabric} {_garment}".strip()
    
    strict_prompt = (
        f"Use the uploaded person as the identity reference. Keep the person's face, "
        f"hairstyle, skin tone, body shape, proportions, expression and pose unchanged. "
        f"Replace only the clothing with: {outfit_desc}. Generate a realistic, high-quality "
        f"virtual try-on. Preserve lighting and image realism."
    )

    logger.info("[tryon] Attempting real virtual try-on with HF Spaces")
    result = await try_on_with_spaces(person_image_bytes, garment_image_bytes, prompt=strict_prompt)
    if result and len(result) > 500:
        logger.info("[tryon] Real virtual try-on succeeded (%d bytes)", len(result))
        return result, "hf-space-vton"

    # Virtual try-on failed after retries. Throw error to enforce failure instead of fallback.
    raise RuntimeError("vton_failed")

