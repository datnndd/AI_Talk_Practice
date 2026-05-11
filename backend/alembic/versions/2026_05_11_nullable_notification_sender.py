"""Allow system notifications without sender

Revision ID: 2026_05_11_nullable_notification_sender
Revises: 2026_05_11_remove_character_thumbnail_url
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_11_nullable_notification_sender"
down_revision: Union[str, None] = "2026_05_11_remove_character_thumbnail_url"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "notifications" in inspector.get_table_names() and _has_column(inspector, "notifications", "sender_user_id"):
        op.alter_column("notifications", "sender_user_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "notifications" in inspector.get_table_names() and _has_column(inspector, "notifications", "sender_user_id"):
        op.alter_column("notifications", "sender_user_id", existing_type=sa.Integer(), nullable=False)
