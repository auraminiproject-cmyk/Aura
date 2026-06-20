import base64

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.agent.tailor_guide import generate_tailoring_guide
from services.api.core.security import get_current_user_id

router = APIRouter()


class TailorRequest(BaseModel):
    garment_type: str = Field(..., min_length=2)
    fabric: str = "silk"
    measurements: dict = Field(default_factory=dict)
    occasion: str | None = None


@router.post("/guide")
async def tailoring_guide(body: TailorRequest, _user_id: str = Depends(get_current_user_id)):
    pdf_bytes = await generate_tailoring_guide(
        garment_type=body.garment_type,
        fabric=body.fabric,
        measurements=body.measurements or {"chest_cm": 88, "waist_cm": 72, "hip_cm": 96},
        occasion=body.occasion,
    )
    return {
        "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
        "content_type": "application/pdf",
    }
