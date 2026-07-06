import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.core.database import get_db
from services.api.core.moderation import moderate_text
from services.api.core.models import Session
from services.api.core.rate_limit import limiter
from services.api.core.security import get_current_user_id
from services.agent.graph import run_graph

router = APIRouter()


class DesignSessionRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=4000)
    language: str = "te"
    num_variants: int = Field(default=4, ge=1, le=6)


@router.post("/design-flow")
@limiter.limit("10/minute")
async def full_design_flow(
    request: Request,
    body: DesignSessionRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    ok, reason = moderate_text(body.message)
    if not ok:
        return {"error": reason, "blocked": True}

    session_id = str(uuid.uuid4())
    db.add(Session(id=session_id, user_id=user_id, status="active"))
    await db.commit()

    result = await run_graph(
        message=body.message,
        user_id=user_id,
        session_id=session_id,
        language=body.language,
        image_b64=None
    )
    return {"session_id": session_id, **result}
