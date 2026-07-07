import os

def fix_design_py():
    path = r'd:\Aura-gem\fashion-ai\services\api\api\v1\design.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old = """    # Auto-fetch stored body profile if none provided
    if not smplx_params:
        result = await db.execute(
            select(BodyProfile)
            .where(BodyProfile.user_id == user_id)
            .order_by(BodyProfile.created_at.desc())
            .limit(1)
        )
        profile = result.scalars().first()
        if profile and profile.smplx_params:
            smplx_params = profile.smplx_params

    result = await generate_outfits(
        design_brief=body.brief,
        smplx_params=smplx_params,
        num_variants=body.num_variants,
    )"""

    new = """    # Auto-fetch stored body profile if none provided
    user_gender = None
    user_photo_b64 = None
    if not smplx_params:
        result = await db.execute(
            select(BodyProfile)
            .where(BodyProfile.user_id == user_id)
            .order_by(BodyProfile.created_at.desc())
            .limit(1)
        )
        profile = result.scalars().first()
        if profile:
            if profile.smplx_params:
                smplx_params = profile.smplx_params
            user_gender = profile.gender
            if profile.measurements and isinstance(profile.measurements, dict) and "_front_photo_b64" in profile.measurements:
                user_photo_b64 = profile.measurements["_front_photo_b64"]

    result = await generate_outfits(
        design_brief=body.brief,
        smplx_params=smplx_params,
        num_variants=body.num_variants,
        user_gender=user_gender,
        user_photo_b64=user_photo_b64,
    )"""
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_generate_outfit_py():
    path = r'd:\Aura-gem\fashion-ai\services\vision\generate_outfit.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_sig = """async def generate_outfits(
    *,
    design_brief: str,
    smplx_params: dict | None = None,
    num_variants: int = 4,
    clip_threshold: float = 0.28,
) -> OutfitGenerationResult:"""
    new_sig = """async def generate_outfits(
    *,
    design_brief: str,
    smplx_params: dict | None = None,
    num_variants: int = 4,
    clip_threshold: float = 0.28,
    user_gender: str | None = None,
    user_photo_b64: str | None = None,
) -> OutfitGenerationResult:"""
    content = content.replace(old_sig, new_sig)

    old_loop = """    for i in range(min(num_variants, len(_PROMPT_TEMPLATES))):
        prompt = _PROMPT_TEMPLATES[i].format(brief=design_brief)

        # Try HF Inference API for SDXL
        if settings.huggingface_api_key and hf_breaker.current_state != "open":
            try:
                image_bytes = await _hf_sdxl_generate(prompt, settings)
                if image_bytes and len(image_bytes) > 500:
                    variants.append(OutfitVariant(
                        image_base64=base64.b64encode(image_bytes).decode("ascii"),
                        prompt=prompt,
                        clip_score=0.0,  # Real score: computed below if FashionCLIP available
                    ))
                    continue
            except Exception as exc:"""

    new_loop = """    from services.vision.tryon import virtual_tryon

    gender_suffix = ""
    if user_gender and user_gender.lower() not in ["neutral", ""]:
        gender_suffix = f", worn by a {user_gender} model, photorealistic face"

    for i in range(min(num_variants, len(_PROMPT_TEMPLATES))):
        prompt = _PROMPT_TEMPLATES[i].format(brief=design_brief) + gender_suffix

        # Try HF Inference API for SDXL
        if settings.huggingface_api_key and hf_breaker.current_state != "open":
            try:
                image_bytes = await _hf_sdxl_generate(prompt, settings)
                if image_bytes and len(image_bytes) > 500:
                    outfit_b64 = base64.b64encode(image_bytes).decode("ascii")
                    
                    if user_photo_b64:
                        try:
                            # Apply virtual try-on automatically if user photo is available
                            tryon_res = await virtual_tryon(outfit_image_b64=outfit_b64, user_photo_b64=user_photo_b64)
                            if tryon_res and "result_image_base64" in tryon_res:
                                outfit_b64 = tryon_res["result_image_base64"]
                        except Exception as e:
                            logger.error(f"Tryon failed during generation: {e}")

                    variants.append(OutfitVariant(
                        image_base64=outfit_b64,
                        prompt=prompt,
                        clip_score=0.0,
                    ))
                    continue
            except Exception as exc:"""
    content = content.replace(old_loop, new_loop)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_tryon_py():
    path = r'd:\Aura-gem\fashion-ai\services\vision\tryon.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_kolors = """async def _kolors_tryon(outfit_b64: str, user_b64: str, settings) -> str | None:
    \"\"\"Call Kolors VTON via HF Spaces Gradio API.\"\"\"
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
        return None"""

    new_kolors = """async def _kolors_tryon(outfit_b64: str, user_b64: str, settings) -> str | None:
    \"\"\"Call IDM-VTON via HF Spaces Gradio Client.\"\"\"
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

    return await asyncio.to_thread(run_vton)"""
    
    content = content.replace(old_kolors, new_kolors)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

fix_design_py()
fix_generate_outfit_py()
fix_tryon_py()
