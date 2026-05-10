"""remove user lesson counters

Revision ID: 2026_05_10_remove_user_lesson_counters
Revises: 2026_05_10_merge_curriculum_units_and_daily_checkins
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_10_remove_user_lesson_counters"
down_revision: Union[str, None] = "2026_05_10_merge_curriculum_units_and_daily_checkins"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REMOVED_COLUMNS = (
    "total_lessons_completed",
    "total_speaking_lessons_completed",
    "total_vocabulary_lessons_completed",
    "perfect_score_count",
    "total_practice_minutes",
)


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_table(inspector, "users"):
        return

    with op.batch_alter_table("users") as batch_op:
        for column_name in REMOVED_COLUMNS:
            if _has_column(inspector, "users", column_name):
                batch_op.drop_column(column_name)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_table(inspector, "users"):
        return

    columns = {
        column_name: sa.Column(column_name, sa.Integer(), nullable=False, server_default="0")
        for column_name in REMOVED_COLUMNS
    }
    with op.batch_alter_table("users") as batch_op:
        for column_name, column in columns.items():
            if not _has_column(inspector, "users", column_name):
                batch_op.add_column(column)
