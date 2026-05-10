import re
import uuid
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.infra.supabase_storage import supabase_storage
from app.modules.users.models.user import User
from app.modules.users.serializers import serialize_user
from app.modules.users.schemas.user import ChangePasswordRequest, ProfileUpdateRequest, UserRead
from app.modules.users.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])
AVATAR_UPLOAD_MAX_BYTES = 5 * 1024 * 1024

@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return serialize_user(user)

@router.patch("/me", response_model=UserRead)
async def update_profile(body: ProfileUpdateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    updated_user = await UserService.update_profile(db, user, body)
    return serialize_user(updated_user)


async def _upload_avatar_image(file: UploadFile, user: User) -> str:
    normalized_content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if not normalized_content_type.startswith("image/"):
        raise BadRequestError("Uploaded avatar must be an image file")

    content = await file.read()
    if len(content) > AVATAR_UPLOAD_MAX_BYTES:
        raise BadRequestError("Avatar image must be 5MB or smaller")

    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else normalized_content_type.split("/", 1)[1]
    safe_extension = re.sub(r"[^a-zA-Z0-9]", "", extension or "jpg")[:12] or "jpg"
    path = f"avatars/{user.id}/{uuid.uuid4().hex}.{safe_extension}"

    result = await supabase_storage.upload_public_object(
        bucket=settings.supabase_images_bucket,
        path=path,
        content=content,
        content_type=normalized_content_type,
    )

    return result.public_url


def _avatar_storage_path_from_url(url: str | None) -> str | None:
    if not url or not settings.supabase_url:
        return None
    parsed = urlparse(url)
    storage_prefix = f"/storage/v1/object/public/{settings.supabase_images_bucket}/"
    if parsed.netloc != urlparse(settings.supabase_url).netloc or not parsed.path.startswith(storage_prefix):
        return None
    path = unquote(parsed.path[len(storage_prefix):])
    return path if path.startswith("avatars/") else None


async def _delete_avatar_by_url(url: str | None) -> None:
    path = _avatar_storage_path_from_url(url)
    if path and supabase_storage.is_configured:
        await supabase_storage.delete_object(bucket=settings.supabase_images_bucket, path=path)


@router.post("/me/avatar", response_model=UserRead, status_code=status.HTTP_200_OK)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    old_avatar = user.avatar
    avatar_url = await _upload_avatar_image(file, user)
    try:
        user.avatar = avatar_url
        await db.commit()
        await db.refresh(user)
    except Exception:
        await _delete_avatar_by_url(avatar_url)
        raise
    await _delete_avatar_by_url(old_avatar)
    return serialize_user(user)


@router.patch("/me/with-avatar", response_model=UserRead)
async def update_profile_with_avatar(
    display_name: str | None = Form(default=None),
    avatar: str | None = Form(default=None),
    age: int | None = Form(default=None),
    level: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    old_avatar = user.avatar
    uploaded_avatar_url = await _upload_avatar_image(file, user) if file is not None else None
    profile_values = {
        "display_name": display_name,
        "avatar": uploaded_avatar_url or avatar,
        "age": age,
        "level": level,
    }
    body = ProfileUpdateRequest(**{key: value for key, value in profile_values.items() if value is not None})
    try:
        updated_user = await UserService.update_profile(db, user, body)
    except Exception:
        await _delete_avatar_by_url(uploaded_avatar_url)
        raise
    if uploaded_avatar_url:
        await _delete_avatar_by_url(old_avatar)
    return serialize_user(updated_user)


@router.post("/me/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await UserService.change_password(db, user, body)
    return {"detail": "Password updated successfully."}
