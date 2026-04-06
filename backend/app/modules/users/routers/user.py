from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.users.models.user import User
from app.modules.users.serializers import serialize_user
from app.modules.users.schemas.user import ChangePasswordRequest, ProfileUpdateRequest, UserRead
from app.modules.users.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return serialize_user(user)

@router.patch("/me", response_model=UserRead)
async def update_profile(body: ProfileUpdateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    updated_user = await UserService.update_profile(db, user, body)
    return serialize_user(updated_user)


@router.post("/me/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await UserService.change_password(db, user, body)
    return {"detail": "Password updated successfully."}
