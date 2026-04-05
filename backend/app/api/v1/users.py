from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.serializers import serialize_user
from app.schemas.user import OnboardingRequest, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return serialize_user(user)

@router.patch("/me", response_model=UserRead)
async def update_profile(body: OnboardingRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    updated_user = await UserService.onboard_or_update(db, user, body)
    return serialize_user(updated_user)
