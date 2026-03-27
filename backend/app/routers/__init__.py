"""
Auth API router — register, login, me.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse, OnboardingRequest
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name="",
        native_language="en",
        target_language="en",
        level="beginner",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user

@router.put("/me/onboard", response_model=UserResponse)
async def onboard(body: OnboardingRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if getattr(user, "is_onboarding_completed", False):
        raise HTTPException(status_code=400, detail="Onboarding already completed")
        
    user.display_name = body.display_name
    user.native_language = body.native_language
    user.avatar = body.avatar
    user.age = body.age
    user.level = body.level
    user.learning_purpose = body.learning_purpose
    user.main_challenge = body.main_challenge
    user.favorite_topics = body.favorite_topics
    user.daily_goal = body.daily_goal
    user.is_onboarding_completed = True
    
    await db.commit()
    await db.refresh(user)
    
    return user
