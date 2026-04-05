from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models.user import User
from app.modules.users.schemas import OnboardingRequest
from app.core.exceptions import BadRequestError

logger = logging.getLogger(__name__)

class UserService:
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
