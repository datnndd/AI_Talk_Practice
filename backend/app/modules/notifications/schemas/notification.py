from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: int
    audience: str
    recipient_user_id: int | None = None
    title: str
    body: str
    created_at: datetime
    read_at: datetime | None = None


class NotificationListResponse(BaseModel):
    items: list[NotificationRead]
    total: int
    page: int
    page_size: int
