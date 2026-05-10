"""drop lesson required flag

Revision ID: 2026_05_10_drop_lesson_required
Revises: 2026_05_10_fix_vietnamese_lesson_text
Create Date: 2026-05-10 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_10_drop_lesson_required"
down_revision: Union[str, None] = "2026_05_10_fix_vietnamese_lesson_text"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return _has_table(inspector, table_name) and any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_column(inspector, "lessons", "is_required"):
        return
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.drop_column("is_required")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _has_column(inspector, "lessons", "is_required"):
        return
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.add_column(sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")))
