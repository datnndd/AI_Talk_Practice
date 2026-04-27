"""remove admin audit logs

Revision ID: 2026_04_27_remove_admin_audit_logs
Revises: 2026_04_27_simplify_gamification_checkin_shop
Create Date: 2026-04-27 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_27_remove_admin_audit_logs"
down_revision: Union[str, None] = "2026_04_27_simplify_gamification_checkin_shop"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "admin_audit_logs", "ix_admin_audit_logs_actor_created"):
        op.drop_index("ix_admin_audit_logs_actor_created", table_name="admin_audit_logs")
    if _has_index(inspector, "admin_audit_logs", "ix_admin_audit_logs_created_at"):
        op.drop_index("ix_admin_audit_logs_created_at", table_name="admin_audit_logs")
    if _has_table(inspector, "admin_audit_logs"):
        op.drop_table("admin_audit_logs")


def downgrade() -> None:
    pass
