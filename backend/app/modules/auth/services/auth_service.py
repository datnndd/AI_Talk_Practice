from __future__ import annotations
import httpx
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.password_policy import validate_password_policy
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.core.config import settings
from app.modules.auth.models.email_otp import EmailOTP
from app.modules.users.models.user import User
from app.modules.users.models.subscription import Subscription
from app.modules.users.repository import UserRepository
from app.modules.auth.schemas.auth import AuthIdentityResponse, LoginRequest, RegisterRequest, TokenResponse, TokenRefreshResponse, RegisterVerifyRequest
from app.infra.email import send_password_reset_email, send_register_otp_email

logger = logging.getLogger(__name__)

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5

class AuthService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        return await UserRepository.get_active_by_id(db, user_id)

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
        kwargs.setdefault("level", "beginner")

        user = await UserRepository.create(db, **kwargs)
        sub = Subscription(user_id=user.id, tier="FREE", status="active", features={})
        db.add(sub)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def register(db: AsyncSession, body: RegisterRequest) -> TokenResponse:
        raise BadRequestError("Please verify your email with OTP before creating a password.")

    @staticmethod
    async def request_otp(db: AsyncSession, email: str, purpose: str) -> None:
        normalized_email = email.strip().lower()
        if purpose == "register" and await UserRepository.get_active_by_email(db, normalized_email):
            raise BadRequestError("Email already registered")
        if purpose == "reset_password" and not await UserRepository.get_active_by_email(db, normalized_email):
            return

        code = f"{secrets.randbelow(1_000_000):06d}"
        otp = EmailOTP(
            email=normalized_email,
            code_hash=hash_password(code),
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES),
        )
        db.add(otp)
        await db.commit()

        if purpose == "register":
            await send_register_otp_email(normalized_email, code)
        else:
            await send_password_reset_email(normalized_email, code)

    @staticmethod
    async def register_with_otp(db: AsyncSession, body: RegisterVerifyRequest) -> TokenResponse:
        normalized_email = body.email.strip().lower()
        if await UserRepository.get_active_by_email(db, normalized_email):
            raise BadRequestError("Email already registered")
        validate_password_policy(body.password)
        await AuthService._assert_consumed_otp(db, normalized_email, "register", body.otp)
        user = await AuthService._create_user_with_free_tier(
            db,
            email=normalized_email,
            display_name=(body.name or "").strip(),
            password_hash=hash_password(body.password),
            auth_provider="local",
            is_email_verified=True,
        )
        logger.info("Registered user id=%s (local, otp verified)", user.id)
        return AuthService._create_token_response(user.id)

    @staticmethod
    async def identify_email(db: AsyncSession, email: str) -> AuthIdentityResponse:
        user = await UserRepository.get_active_by_email(db, email)
        return AuthIdentityResponse(status="existing" if user else "new")

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

            if not email or not google_uid:
                raise UnauthorizedError("Google account did not provide required profile information")

            email = email.strip().lower()
            user = await UserRepository.get_active_by_google_id(db, google_uid)
            if not user:
                user = await UserRepository.get_active_by_email(db, email)
            if not user:
                user = await AuthService._create_user_with_free_tier(
                    db,
                    email=email,
                    display_name=display_name,
                    avatar=picture,
                    auth_provider="google",
                    google_id=google_uid,
                    password_hash=None,
                    is_email_verified=True,
                )
            else:
                user.google_id = user.google_id or google_uid
                if user.auth_provider != "google":
                    user.auth_provider = "google"
                if picture and not user.avatar:
                    user.avatar = picture
                if display_name and not user.display_name:
                    user.display_name = display_name
                user.is_email_verified = True
                await db.commit()
            
            return AuthService._create_token_response(user.id)
        except UnauthorizedError:
            raise
        except SQLAlchemyError:
            await db.rollback()
            logger.exception("Google login failed during database update")
            raise UnauthorizedError("Google authentication failed")
        except Exception as e:
            await db.rollback()
            logger.exception("Google login failed: %s", str(e) or e.__class__.__name__)
            raise UnauthorizedError("Google authentication failed")

    @staticmethod
    async def request_password_reset(db: AsyncSession, email: str) -> None:
        await AuthService.request_otp(db, email, "reset_password")

    @staticmethod
    async def reset_password(db: AsyncSession, email: str, otp: str, new_password: str) -> None:
        normalized_email = email.strip().lower()
        user = await UserRepository.get_active_by_email(db, normalized_email)
        if not user:
            raise BadRequestError("Invalid or expired OTP")
        validate_password_policy(new_password)
        await AuthService._consume_otp(db, normalized_email, "reset_password", otp)
        user.password_hash = hash_password(new_password)
        if user.auth_provider == "google":
            user.auth_provider = "local"
        user.is_email_verified = True
        await db.commit()

    @staticmethod
    async def _consume_otp(db: AsyncSession, email: str, purpose: str, code: str) -> EmailOTP:
        result = await db.execute(
            select(EmailOTP)
            .where(EmailOTP.email == email)
            .where(EmailOTP.purpose == purpose)
            .where(EmailOTP.consumed_at.is_(None))
            .order_by(EmailOTP.created_at.desc())
        )
        otp = result.scalars().first()
        now = datetime.now(timezone.utc)
        if not otp:
            raise BadRequestError("Invalid or expired OTP")
        expires_at = otp.expires_at.replace(tzinfo=timezone.utc) if otp.expires_at.tzinfo is None else otp.expires_at.astimezone(timezone.utc)
        if expires_at < now or otp.attempt_count >= OTP_MAX_ATTEMPTS:
            raise BadRequestError("Invalid or expired OTP")
        if not verify_password(code, otp.code_hash):
            otp.attempt_count += 1
            await db.commit()
            raise BadRequestError("Invalid or expired OTP")
        otp.consumed_at = now
        await db.commit()
        return otp

    @staticmethod
    async def verify_otp(db: AsyncSession, email: str, purpose: str, code: str) -> None:
        await AuthService._consume_otp(db, email.strip().lower(), purpose, code)

    @staticmethod
    async def _assert_consumed_otp(db: AsyncSession, email: str, purpose: str, code: str) -> None:
        result = await db.execute(
            select(EmailOTP)
            .where(EmailOTP.email == email)
            .where(EmailOTP.purpose == purpose)
            .where(EmailOTP.consumed_at.is_not(None))
            .order_by(EmailOTP.consumed_at.desc())
        )
        otp = result.scalars().first()
        now = datetime.now(timezone.utc)
        if not otp:
            raise BadRequestError("Invalid or expired OTP")
        expires_at = otp.expires_at.replace(tzinfo=timezone.utc) if otp.expires_at.tzinfo is None else otp.expires_at.astimezone(timezone.utc)
        if expires_at < now or not verify_password(code, otp.code_hash):
            raise BadRequestError("Invalid or expired OTP")

    @staticmethod
    async def verify_email(db: AsyncSession, token: str) -> None:
        user_id = decode_token(token)
        if not user_id or not (user := await UserRepository.get_active_by_id(db, user_id)):
            raise BadRequestError("Invalid or expired verification token")
        user.is_active = True
        await db.commit()
