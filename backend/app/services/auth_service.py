from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import OnboardingRequest

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, body: RegisterRequest) -> str:
        existing = await UserRepository.get_active_by_email(db, body.email)
        if existing:
            raise BadRequestError("Email already registered")

        user = await UserRepository.create(
            db,
            email=body.email,
            password_hash=hash_password(body.password),
            display_name="",
            native_language="en",
            target_language="en",
            level="beginner",
        )
        await db.commit()
        await db.refresh(user)
        logger.info("Registered user id=%s", user.id)
        return create_access_token(user.id)

    @staticmethod
    async def login(db: AsyncSession, body: LoginRequest) -> str:
        user = await UserRepository.get_active_by_email(db, body.email)
        if not user or not verify_password(body.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        return create_access_token(user.id)

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        return await UserRepository.get_active_by_id(db, user_id)

    @staticmethod
    async def onboard(db: AsyncSession, user: User, body: OnboardingRequest) -> User:
        if user.is_onboarding_completed:
            raise BadRequestError("Onboarding already completed")

        user.display_name = body.display_name
        user.native_language = body.native_language
        if body.target_language is not None:
            user.target_language = body.target_language
        user.avatar = body.avatar
        user.age = body.age
        user.level = body.level
        user.learning_purpose = body.learning_purpose
        user.main_challenge = body.main_challenge
        user.favorite_topics = body.favorite_topics
        user.daily_goal = body.daily_goal
        if body.preferences is not None:
            user.preferences = body.preferences
        user.is_onboarding_completed = True

        await db.commit()
        await db.refresh(user)
        logger.info("Completed onboarding for user id=%s", user.id)
        return user
