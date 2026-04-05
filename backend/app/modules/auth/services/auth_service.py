from __future__ import annotations
import httpx
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.core.config import settings
from app.modules.users.models.user import User
from app.modules.users.models.subscription import Subscription
from app.modules.users.repository import UserRepository
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, TokenRefreshResponse
from app.infra.email import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def _create_token_response(user_id: int) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
            token_type="bearer"
        )

    @staticmethod
    async def _create_user_with_free_tier(db: AsyncSession, **kwargs) -> User:
        """Centralized helper to create a user and assign a free subscription."""
        kwargs.setdefault("display_name", "")
        kwargs.setdefault("native_language", "en")
        kwargs.setdefault("target_language", "en")
        kwargs.setdefault("level", "beginner")

        user = await UserRepository.create(db, **kwargs)
        sub = Subscription(user_id=user.id, tier="FREE", status="active", features={})
        db.add(sub)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def register(db: AsyncSession, body: RegisterRequest) -> TokenResponse:
        if await UserRepository.get_active_by_email(db, body.email):
            raise BadRequestError("Email already registered")

        user = await AuthService._create_user_with_free_tier(
            db,
            email=body.email,
            password_hash=hash_password(body.password),
            auth_provider="local"
        )
        await send_verification_email(user.email, create_access_token(user.id))
        logger.info("Registered user id=%s (local)", user.id)
        return AuthService._create_token_response(user.id)

    @staticmethod
    async def login(db: AsyncSession, body: LoginRequest) -> TokenResponse:
        user = await UserRepository.get_active_by_email(db, body.email)
        if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        return AuthService._create_token_response(user.id)

    @staticmethod
    async def refresh(db: AsyncSession, refresh_token: str) -> TokenRefreshResponse:
        user_id = decode_token(refresh_token, expected_type="refresh")
        if not user_id or not (user := await UserRepository.get_active_by_id(db, user_id)):
            raise UnauthorizedError("Invalid or expired refresh token")
        return TokenRefreshResponse(
            access_token=create_access_token(user.id),
            token_type="bearer"
        )
        
    @staticmethod
    async def google_login(db: AsyncSession, google_token: str) -> TokenResponse:
        try:
            if google_token.count('.') == 2:
                idinfo = id_token.verify_oauth2_token(
                    google_token, 
                    google_requests.Request(), 
                    settings.google_client_id
                )
                google_uid, email = idinfo['sub'], idinfo.get('email')
                display_name = idinfo.get('name', '')
                picture = idinfo.get('picture', '')
            else:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {google_token}"}
                    )
                    resp.raise_for_status()
                    idinfo = resp.json()
                    google_uid, email = idinfo['sub'], idinfo.get('email')
                    display_name = idinfo.get('name', '')
                    picture = idinfo.get('picture', '')

            user = await UserRepository.get_active_by_email(db, email)
            if not user:
                user = await AuthService._create_user_with_free_tier(
                    db,
                    email=email,
                    display_name=display_name,
                    avatar=picture,
                    auth_provider="google",
                    password_hash=None
                )
            elif user.auth_provider != "google":
                user.auth_provider = "google"
                await db.commit()
            
            return AuthService._create_token_response(user.id)
        except Exception as e:
            logger.error("Google login failed: %s", str(e))
            raise UnauthorizedError("Google authentication failed")

    @staticmethod
    async def request_password_reset(db: AsyncSession, email: str) -> None:
        user = await UserRepository.get_active_by_email(db, email)
        if not user: return
        reset_token = create_access_token(user.id)
        await send_password_reset_email(user.email, reset_token)

    @staticmethod
    async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
        user_id = decode_token(token)
        if not user_id or not (user := await UserRepository.get_active_by_id(db, user_id)):
            raise BadRequestError("Invalid or expired reset token")
        user.password_hash = hash_password(new_password)
        await db.commit()

    @staticmethod
    async def verify_email(db: AsyncSession, token: str) -> None:
        user_id = decode_token(token)
        if not user_id or not (user := await UserRepository.get_active_by_id(db, user_id)):
            raise BadRequestError("Invalid or expired verification token")
        user.is_active = True
        await db.commit()
