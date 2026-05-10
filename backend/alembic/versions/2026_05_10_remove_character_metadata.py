"""remove character metadata

Revision ID: 2026_05_10_remove_character_metadata
Revises: 2026_05_10_remove_user_lesson_counters
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_10_remove_character_metadata"
down_revision: Union[str, None] = "2026_05_10_remove_user_lesson_counters"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_column(inspector, "characters", "metadata"):
        return

    with op.batch_alter_table("characters") as batch_op:
        batch_op.drop_column("metadata")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_column(inspector, "characters", "metadata"):
        return

    with op.batch_alter_table("characters") as batch_op:
        batch_op.add_column(sa.Column("metadata", sa.JSON(), nullable=True, server_default="{}"))
