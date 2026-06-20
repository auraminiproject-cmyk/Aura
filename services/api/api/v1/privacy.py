import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.core.database import get_db
from services.api.core.models import BodyProfile, Conversation, Session, StyleProfile, User, WardrobeItem
from services.api.core.security import get_current_user_id

router = APIRouter()


@router.get("/export")
async def export_user_data(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """GDPR/CCPA data export — all user-linked rows."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    sessions = (await db.execute(select(Session).where(Session.user_id == user_id))).scalars().all()
    session_ids = [s.id for s in sessions]
    conversations = []
    if session_ids:
        conversations = (
            await db.execute(select(Conversation).where(Conversation.session_id.in_(session_ids)))
        ).scalars().all()
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {"id": user.id if user else user_id, "display_name": user.display_name if user else None},
        "sessions": [{"id": s.id, "created_at": str(s.created_at)} for s in sessions],
        "conversations": [{"role": c.role, "content": c.content, "language": c.language} for c in conversations],
        "body_profiles": [
            {"id": b.id, "measurements": b.measurements}
            for b in (await db.execute(select(BodyProfile).where(BodyProfile.user_id == user_id))).scalars().all()
        ],
        "style_profile": (
            await db.execute(select(StyleProfile).where(StyleProfile.user_id == user_id))
        ).scalar_one_or_none(),
        "wardrobe": [
            {"name": w.name, "category": w.category}
            for w in (await db.execute(select(WardrobeItem).where(WardrobeItem.user_id == user_id))).scalars().all()
        ],
    }


@router.post("/consent")
async def record_consent(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id, "consent": True, "recorded_at": datetime.now(timezone.utc).isoformat()}
