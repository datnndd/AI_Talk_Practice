from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.notifications.schemas.notification import (
    NotificationListResponse,
    NotificationRead,
)
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.users.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_my_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = await NotificationService.list_for_user(db, user=user, page=page, page_size=page_size)
    return NotificationListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await NotificationService.mark_read(db, user=user, notification_id=notification_id)
