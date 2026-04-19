from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.admin.schemas.audit_log import AdminAuditLogListResponse
from app.modules.admin.services.audit_log_service import AdminAuditLogService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/audit-logs", tags=["admin"])


@router.get("", response_model=AdminAuditLogListResponse)
async def list_admin_audit_logs(
    action: str | None = Query(default=None),
    actor_user_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    logs, total = await AdminAuditLogService.list_logs(
        db,
        action=action,
        actor_user_id=actor_user_id,
        page=page,
        page_size=page_size,
    )
    return AdminAuditLogListResponse(items=logs, total=total, page=page, page_size=page_size)
