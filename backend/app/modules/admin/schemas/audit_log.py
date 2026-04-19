from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AdminAuditLogRead(BaseModel):
    id: int
    actor_user_id: int
    action: str
    entity_type: str
    entity_id: str | None = None
    target_user_id: int | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminAuditLogListResponse(BaseModel):
    items: list[AdminAuditLogRead]
    total: int
    page: int
    page_size: int
