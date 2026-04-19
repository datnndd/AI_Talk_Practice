from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AdminNotificationCreateRequest(BaseModel):
    audience: Literal["all", "users"]
    recipient_user_ids: list[int] | None = None
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_audience(self) -> "AdminNotificationCreateRequest":
        if self.audience == "users" and not self.recipient_user_ids:
            raise ValueError("recipient_user_ids is required for users audience")
        return self


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


class AdminNotificationCreateResponse(BaseModel):
    items: list[NotificationRead]
