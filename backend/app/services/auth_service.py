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
from app.models.user import User
from app.models.subscription import Subscription
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, TokenRefreshResponse
from app.services.email import send_verification_email, send_password_reset_email

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
        # Set default values if missing to avoid duplicate argument issues
        kwargs.setdefault("display_name", "")
        kwargs.setdefault("native_language", "en")
        kwargs.setdefault("target_language", "en")
        kwargs.setdefault("level", "beginner")

        user = await UserRepository.create(db, **kwargs)
        # Provision FREE subscription
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
        # Send verification email asynchronously
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
            # Determine if it's an ID Token (JWT) or an Access Token (Opaque)
            if google_token.count('.') == 2:
                # ID Token verify
                idinfo = id_token.verify_oauth2_token(
                    google_token, 
                    google_requests.Request(), 
                    settings.google_client_id
                )
                google_uid, email = idinfo['sub'], idinfo.get('email')
                display_name = idinfo.get('name', '')
                picture = idinfo.get('picture', '')
            else:
                # Access Token verify via userinfo API
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {google_token}"}
                    )
                    if resp.status_code != 200:
                        raise UnauthorizedError("Invalid Google access token")
                    user_info = resp.json()
                    google_uid, email = user_info['sub'], user_info.get('email')
                    display_name = user_info.get('name', '')
                    picture = user_info.get('picture', '')
            
            if not email:
                raise BadRequestError("Email not provided by Google")

            # 1. Try by google_id
            user = await UserRepository.get_active_by_google_id(db, google_uid)
            
            # 2. If not found, try by email to link
            if not user:
                user = await UserRepository.get_active_by_email(db, email)
                if user:
                    user.google_id, user.auth_provider = google_uid, "google"
                    user.is_email_verified = True
                    await db.commit()
                else:
                    # 3. Create new user
                    user = await AuthService._create_user_with_free_tier(
                        db,
                        email=email,
                        google_id=google_uid,
                        auth_provider="google",
                        display_name=display_name,
                        avatar=picture,
                        is_email_verified=True
                    )
                    logger.info("New User id=%s via Google", user.id)
                    
            return AuthService._create_token_response(user.id)
        except ValueError as e:
            logger.error(f"Google verify error: {e}")
            raise UnauthorizedError("Invalid Google token")

    @staticmethod
    async def request_password_reset(db: AsyncSession, email: str) -> None:
        if user := await UserRepository.get_active_by_email(db, email):
            await send_password_reset_email(user.email, create_access_token(user.id))

    @staticmethod
    async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
        user_id = decode_token(token, expected_type="access")
        if not user_id or not (user := await UserRepository.get_active_by_id(db, user_id)):
            raise BadRequestError("Invalid or expired reset token")
            
        user.password_hash = hash_password(new_password)
        await db.commit()

    @staticmethod
    async def verify_email(db: AsyncSession, token: str) -> None:
        user_id = decode_token(token, expected_type="access")
        if not user_id or not (user := await UserRepository.get_active_by_id(db, user_id)):
            raise BadRequestError("Invalid or expired verification token")
            
        if not user.is_email_verified:
            user.is_email_verified = True
            await db.commit()
