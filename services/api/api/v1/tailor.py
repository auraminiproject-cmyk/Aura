import base64

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.agent.tailor_guide import generate_tailoring_guide
from services.api.core.database import get_db
from services.api.core.models import BodyProfile
from services.api.core.security import get_current_user_id

router = APIRouter()


class TailorRequest(BaseModel):
    garment_type: str = Field(..., min_length=2)
    fabric: str = "silk"
    measurements: dict = Field(default_factory=dict)
    occasion: str | None = None


@router.post("/guide")
async def tailoring_guide(
    body: TailorRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate tailoring guide using the user's stored body measurements.

    If no measurements are provided in the request, auto-fetches
    the user's latest body profile from the avatar analysis.
    """
    measurements = body.measurements

    # Auto-fetch stored measurements if none provided
    if not measurements:
        result = await db.execute(
            select(BodyProfile)
            .where(BodyProfile.user_id == user_id)
            .order_by(BodyProfile.created_at.desc())
            .limit(1)
        )
        profile = result.scalars().first()
        if profile and profile.measurements:
            stored = profile.measurements
            # Extract clean measurements (skip metadata keys)
            measurements = {k: v for k, v in stored.items() if not k.startswith("_")}

    # Fallback to generic if still empty
    if not measurements:
        measurements = {"chest_cm": 88, "waist_cm": 72, "hip_cm": 96}

    pdf_bytes = await generate_tailoring_guide(
        garment_type=body.garment_type,
        fabric=body.fabric,
        measurements=measurements,
        occasion=body.occasion,
    )
    return {
        "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
        "content_type": "application/pdf",
    }
