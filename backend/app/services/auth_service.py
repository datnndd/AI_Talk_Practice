from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.user import OnboardingRequest

class AuthService:
    @staticmethod
    async def register(db: AsyncSession, body: RegisterRequest) -> str:
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

        return create_access_token(user.id)

    @staticmethod
    async def login(db: AsyncSession, body: LoginRequest) -> str:
        result = await db.execute(select(User).where(User.email == body.email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return create_access_token(user.id)

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def onboard(db: AsyncSession, user: User, body: OnboardingRequest) -> User:
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
