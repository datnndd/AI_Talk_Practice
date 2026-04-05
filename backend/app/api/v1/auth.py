"""
Auth API router — register, login, refresh, google_oauth, password reset, etc.
"""

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, TokenRefreshResponse,
    RefreshRequest, GoogleLoginRequest, ForgotPasswordRequest,
    ResetPasswordRequest, VerifyEmailRequest
)
from app.schemas.user import UserRead
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return user

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.register(db, body)

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.login(db, body)

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.refresh(db, body.refresh_token)

@router.post("/google", response_model=TokenResponse)
async def google_login(body: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.google_login(db, body.id_token)

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await AuthService.request_password_reset(db, body.email)
    return {"message": "If that email exists, a reset link has been sent"}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await AuthService.reset_password(db, body.token, body.new_password)
    return {"message": "Password updated successfully"}

@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    await AuthService.verify_email(db, body.token)
    return {"message": "Email verified successfully"}
