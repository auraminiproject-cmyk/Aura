import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.core.database import get_db
from services.api.core.models import User
from services.api.core.security import create_access_token, create_refresh_token, decode_token, get_current_user_id

router = APIRouter()


class GuestLoginRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    user_id: str


@router.post("/guest", response_model=TokenResponse)
async def guest_login(body: GuestLoginRequest, db: AsyncSession = Depends(get_db)):
    user = User(id=str(uuid.uuid4()), display_name=body.display_name or "Guest")
    db.add(user)
    await db.commit()
    token = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(access_token=token, refresh_token=refresh, user_id=user.id)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = str(payload.get("sub"))
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        user_id=user_id,
    )


@router.get("/me")
async def me(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "display_name": user.display_name, "email": user.email}
