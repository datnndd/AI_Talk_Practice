from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.users.models.user import User
from app.modules.users.schemas.admin_user import (
    AdminUserListResponse,
    AdminUserRead,
    AdminUserSubscriptionUpdateRequest,
    AdminUserUpdateRequest,
)
from app.modules.users.serializers import serialize_admin_user
from app.modules.users.services.admin_user_service import AdminUserService

router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.get("", response_model=AdminUserListResponse)
async def list_admin_users(
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    role: str | None = Query(default=None),
    subscription_tier: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    users, total = await AdminUserService.list_users(
        db,
        search=search,
        status=status,
        role=role,
        subscription_tier=subscription_tier,
        page=page,
        page_size=page_size,
    )
    return AdminUserListResponse(
        items=[serialize_admin_user(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=AdminUserRead)
async def get_admin_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    user = await AdminUserService.get_user(db, user_id)
    return serialize_admin_user(user)


@router.put("/{user_id}", response_model=AdminUserRead)
async def update_admin_user(
    user_id: int,
    body: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    user = await AdminUserService.update_user(db, user_id=user_id, body=body)
    return serialize_admin_user(user)


@router.post("/{user_id}/toggle-admin", response_model=AdminUserRead)
async def toggle_admin_user_access(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin_user),
):
    user = await AdminUserService.toggle_admin_access(db, actor=actor, user_id=user_id)
    return serialize_admin_user(user)


@router.put("/{user_id}/subscription", response_model=AdminUserRead)
async def update_admin_user_subscription(
    user_id: int,
    body: AdminUserSubscriptionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    user = await AdminUserService.update_subscription(db, user_id=user_id, body=body)
    return serialize_admin_user(user)


@router.post("/{user_id}/deactivate", response_model=AdminUserRead)
async def deactivate_admin_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin_user),
):
    user = await AdminUserService.deactivate_user(db, actor=actor, user_id=user_id)
    return serialize_admin_user(user)


@router.post("/{user_id}/restore", response_model=AdminUserRead)
async def restore_admin_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    user = await AdminUserService.restore_user(db, user_id=user_id)
    return serialize_admin_user(user)
