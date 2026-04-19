from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models.audit_log import AdminAuditLog


class AdminAuditLogService:
    @staticmethod
    def record(
        db: AsyncSession,
        *,
        actor_user_id: int,
        action: str,
        entity_type: str,
        entity_id: str | int | None = None,
        target_user_id: int | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> AdminAuditLog:
        audit_log = AdminAuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            target_user_id=target_user_id,
            before=before,
            after=after,
            reason=reason,
        )
        db.add(audit_log)
        return audit_log

    @staticmethod
    async def list_logs(
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        action: str | None = None,
        actor_user_id: int | None = None,
    ) -> tuple[list[AdminAuditLog], int]:
        stmt = select(AdminAuditLog)
        count_stmt = select(func.count(AdminAuditLog.id))

        if action:
            stmt = stmt.where(AdminAuditLog.action == action)
            count_stmt = count_stmt.where(AdminAuditLog.action == action)
        if actor_user_id:
            stmt = stmt.where(AdminAuditLog.actor_user_id == actor_user_id)
            count_stmt = count_stmt.where(AdminAuditLog.actor_user_id == actor_user_id)

        stmt = stmt.order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        logs = list((await db.execute(stmt)).scalars().all())
        total = int((await db.execute(count_stmt)).scalar_one() or 0)
        return logs, total
