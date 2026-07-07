from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.core.database import get_db
from services.api.core.models import BodyProfile
from services.api.core.security import get_current_user_id
from services.vision.generate_outfit import generate_outfits
from services.vision.tryon import virtual_tryon

router = APIRouter()


class DesignRequest(BaseModel):
    brief: str = Field(..., min_length=3, max_length=2000)
    smplx_params: dict | None = None
    num_variants: int = Field(default=4, ge=1, le=8)


class DesignResponse(BaseModel):
    variants: list[dict]
    preview_ready_ms: int
    full_ready_ms: int


@router.post("/outfits", response_model=DesignResponse)
async def create_outfits(
    body: DesignRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate outfit designs using the user's body profile for personalized fit."""
    smplx_params = body.smplx_params

    # Auto-fetch stored body profile if none provided
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
    )
    return DesignResponse(
        variants=[v.__dict__ for v in result.variants],
        preview_ready_ms=result.preview_ready_ms,
        full_ready_ms=result.full_ready_ms,
    )


class TryOnRequest(BaseModel):
    outfit_image_base64: str
    user_photo_base64: str


@router.post("/tryon")
async def try_on(body: TryOnRequest, _user_id: str = Depends(get_current_user_id)):
    return await virtual_tryon(
        outfit_image_b64=body.outfit_image_base64,
        user_photo_b64=body.user_photo_base64,
    )


# ── VLM Endpoints (C5 — Blueprint Section 4.10) ─────────────────────────────


@router.post("/analyze-image")
async def analyze_clothing(
    image: UploadFile = File(...),
    prompt: str = Form("Analyze this clothing item in detail."),
    language: str = Form("en"),
    _user_id: str = Depends(get_current_user_id),
):
    """Analyze a clothing image using VLM (Groq Vision / Qwen2.5-VL)."""
    from services.agent.vlm import analyze_clothing_image

    image_bytes = await image.read()
    result = await analyze_clothing_image(image_bytes, prompt=prompt, language=language)
    return {
        "description": result.description,
        "tags": result.tags,
        "style_category": result.style_category,
        "color_palette": result.color_palette,
        "suggestions": result.suggestions,
        "provider": result.provider,
        "confidence": result.confidence,
    }


class AnalyzeBase64Request(BaseModel):
    image_base64: str
    prompt: str = "Analyze this clothing item in detail."
    language: str = "en"


@router.post("/analyze-image-b64")
async def analyze_clothing_b64(
    body: AnalyzeBase64Request,
    _user_id: str = Depends(get_current_user_id),
):
    """Analyze a clothing image (base64) using VLM."""
    import base64

    from services.agent.vlm import analyze_clothing_image

    image_bytes = base64.b64decode(body.image_base64)
    result = await analyze_clothing_image(image_bytes, prompt=body.prompt, language=body.language)
    return {
        "description": result.description,
        "tags": result.tags,
        "style_category": result.style_category,
        "color_palette": result.color_palette,
        "suggestions": result.suggestions,
        "provider": result.provider,
        "confidence": result.confidence,
    }


class EvalRequest(BaseModel):
    image_base64: str
    context: str = ""


@router.post("/evaluate-outfit")
async def evaluate_outfit(
    body: EvalRequest,
    _user_id: str = Depends(get_current_user_id),
):
    """Evaluate an outfit image and get scoring + suggestions."""
    import base64

    from services.agent.vlm import evaluate_outfit_image

    image_bytes = base64.b64decode(body.image_base64)
    return await evaluate_outfit_image(image_bytes, context=body.context)

