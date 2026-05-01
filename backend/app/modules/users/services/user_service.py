from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.core.exceptions import BadRequestError
from app.core.password_policy import validate_password_policy
from app.modules.users.models.user import User
from app.modules.users.schemas.user import ChangePasswordRequest, OnboardingRequest, ProfileUpdateRequest

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    async def update_profile(db: AsyncSession, user: User, body: ProfileUpdateRequest) -> User:
        update_data = body.model_dump(exclude_unset=True)
        if not update_data:
            raise BadRequestError("No profile fields were provided")

        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await db.commit()
        await db.refresh(user)
        logger.info("Updated profile for user id=%s", user.id)
        return user

    @staticmethod
    async def onboard_or_update(db: AsyncSession, user: User, body: OnboardingRequest) -> User:
        """
        Cập nhật thông tin profile/onboarding cho user một cách gọn gàng.
        """
        update_data = body.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
            
        user.is_onboarding_completed = True
        await db.commit()
        await db.refresh(user)
        logger.info("Updated profile and completed onboarding for user id=%s", user.id)
        return user

    @staticmethod
    async def change_password(db: AsyncSession, user: User, body: ChangePasswordRequest) -> None:
        if not user.password_hash:
            raise BadRequestError("Please use forgot password OTP flow to set a password.")

        if user.password_hash:
            if not body.current_password:
                raise BadRequestError("Current password is required.")

            if not verify_password(body.current_password, user.password_hash):
                raise BadRequestError("Current password is incorrect.")

        if body.current_password and body.current_password == body.new_password:
            raise BadRequestError("New password must be different from the current password.")

        validate_password_policy(body.new_password)
        user.password_hash = hash_password(body.new_password)
        await db.commit()
        logger.info("Changed password for user id=%s", user.id)
