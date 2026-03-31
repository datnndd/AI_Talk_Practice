"""
Auth API router — register, login, me.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse, OnboardingRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    token = await AuthService.register(db, body)
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    token = await AuthService.login(db, body)
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user

@router.put("/me/onboard", response_model=UserResponse)
async def onboard(body: OnboardingRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    updated_user = await AuthService.onboard(db, user, body)
    return updated_user
