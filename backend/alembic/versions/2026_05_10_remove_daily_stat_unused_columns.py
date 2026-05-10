"""remove daily stat unused columns

Revision ID: 2026_05_10_remove_daily_stat_unused_columns
Revises: 2026_05_10_seed_curriculum_sections
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_10_remove_daily_stat_unused_columns"
down_revision: Union[str, None] = "2026_05_10_seed_curriculum_sections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REMOVED_COLUMNS = (
    "minutes_practiced",
    "speaking_lessons_completed",
    "vocabulary_lessons_completed",
    "daily_goal_met",
    "avg_score",
    "recordings_count",
)


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_table(inspector, "daily_stats"):
        return

    with op.batch_alter_table("daily_stats") as batch_op:
        for column_name in REMOVED_COLUMNS:
            if _has_column(inspector, "daily_stats", column_name):
                batch_op.drop_column(column_name)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_table(inspector, "daily_stats"):
        return

    columns = {
        "minutes_practiced": sa.Column("minutes_practiced", sa.Integer(), nullable=False, server_default="0"),
        "speaking_lessons_completed": sa.Column(
            "speaking_lessons_completed", sa.Integer(), nullable=False, server_default="0"
        ),
        "vocabulary_lessons_completed": sa.Column(
            "vocabulary_lessons_completed", sa.Integer(), nullable=False, server_default="0"
        ),
        "daily_goal_met": sa.Column("daily_goal_met", sa.Boolean(), nullable=False, server_default=sa.false()),
        "avg_score": sa.Column("avg_score", sa.Float(), nullable=True),
        "recordings_count": sa.Column("recordings_count", sa.Integer(), nullable=False, server_default="0"),
    }
    with op.batch_alter_table("daily_stats") as batch_op:
        for column_name, column in columns.items():
            if not _has_column(inspector, "daily_stats", column_name):
                batch_op.add_column(column)
