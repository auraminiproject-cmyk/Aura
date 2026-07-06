import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.core.database import get_db
from services.api.core.models import User, BodyProfile
from services.api.core.security import create_access_token, create_refresh_token, decode_token, get_current_user_id

router = APIRouter()


import bcrypt

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

class SignupRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=6)
    display_name: str | None = Field(default=None, max_length=128)
    gender: str | None = Field(default="Neutral", max_length=16)
    profile_photo_b64: str | None = None

class LoginRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=6)

class GuestLoginRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=128)
    gender: str | None = Field(default="Neutral", max_length=16)
    profile_photo_b64: str | None = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    user_id: str

@router.post("/signup", response_model=TokenResponse)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(body.password)
    user = User(
        id=str(uuid.uuid4()), 
        email=body.email, 
        hashed_password=hashed_password,
        display_name=body.display_name or body.email.split("@")[0],
        gender=body.gender
    )
    db.add(user)
    await db.flush()
    
    if body.profile_photo_b64:
        bp = BodyProfile(
            id=str(uuid.uuid4()),
            user_id=user.id,
            measurements={
                "_front_photo_b64": body.profile_photo_b64,
                "_vlm_gender": body.gender,
                "_pipeline": "profile_photo_signup"
            }
        )
        db.add(bp)
        
    await db.commit()
    
    token = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(access_token=token, refresh_token=refresh, user_id=user.id)

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(access_token=token, refresh_token=refresh, user_id=user.id)

@router.post("/guest", response_model=TokenResponse)
async def guest_login(body: GuestLoginRequest, db: AsyncSession = Depends(get_db)):
    user = User(
        id=str(uuid.uuid4()), 
        display_name=body.display_name or "Guest",
        gender=body.gender
    )
    db.add(user)
    await db.flush()
    
    if body.profile_photo_b64:
        bp = BodyProfile(
            id=str(uuid.uuid4()),
            user_id=user.id,
            measurements={
                "_front_photo_b64": body.profile_photo_b64,
                "_vlm_gender": body.gender,
                "_pipeline": "profile_photo_signup"
            }
        )
        db.add(bp)
        
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
