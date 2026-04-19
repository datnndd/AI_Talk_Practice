from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.notifications.schemas.notification import (
    AdminNotificationCreateRequest,
    AdminNotificationCreateResponse,
    NotificationListResponse,
)
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/notifications", tags=["admin"])


@router.post("", response_model=AdminNotificationCreateResponse, status_code=status.HTTP_201_CREATED)
async def send_admin_notification(
    body: AdminNotificationCreateRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin_user),
):
    items = await NotificationService.create_admin_notifications(db, actor=actor, body=body)
    return AdminNotificationCreateResponse(items=items)


@router.get("", response_model=NotificationListResponse)
async def list_admin_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    items, total = await NotificationService.list_admin_notifications(db, page=page, page_size=page_size)
    return NotificationListResponse(items=items, total=total, page=page, page_size=page_size)
