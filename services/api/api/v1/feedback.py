import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.core.database import get_db
from services.api.core.models import StyleProfile
from services.api.core.security import get_current_user_id

router = APIRouter()


class StyleFeedbackRequest(BaseModel):
    liked: bool
    tags: list[str] = Field(default_factory=list)
    outfit_description: str | None = None


@router.post("/style")
async def update_style_feedback(
    body: StyleFeedbackRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StyleProfile).where(StyleProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    delta = [1.0 if body.liked else -0.5 for _ in (body.tags or ["ethnic"])]
    tag_weights = dict(zip(body.tags or ["ethnic"], delta))

    if profile is None:
        profile = StyleProfile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            preference_vector=[1.0 if body.liked else 0.0],
            liked_tags=list(body.tags) if body.liked else [],
        )
        db.add(profile)
    else:
        vec = list(profile.preference_vector or [0.5])
        vec[0] = min(1.0, max(0.0, vec[0] + (0.1 if body.liked else -0.1)))
        profile.preference_vector = vec
        liked = set(profile.liked_tags or [])
        if body.liked:
            liked.update(body.tags)
        profile.liked_tags = list(liked)

    await db.commit()
    return {
        "user_id": user_id,
        "preference_vector": profile.preference_vector,
        "liked_tags": profile.liked_tags,
        "tag_weights": tag_weights,
    }
