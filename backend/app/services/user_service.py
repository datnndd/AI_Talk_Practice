from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import OnboardingRequest
from app.core.exceptions import BadRequestError

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    async def onboard_or_update(db: AsyncSession, user: User, body: OnboardingRequest) -> User:
        """
        Cập nhật thông tin profile/onboarding cho user một cách gọn gàng.
        Sử dụng model_dump(exclude_unset=True) để chỉ cập nhật các trường có trong request.
        """
        # Tối ưu: Dùng model_dump dể cập nhật tự động các field hợp lệ
        update_data = body.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
            
        user.is_onboarding_completed = True
        await db.commit()
        await db.refresh(user)
        logger.info("Updated profile and completed onboarding for user id=%s", user.id)
        return user
