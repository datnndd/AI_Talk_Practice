"""restore daily checkins

Revision ID: 2026_05_10_restore_daily_checkins
Revises: 2026_05_10_remove_daily_checkins
Create Date: 2026-05-10 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_10_restore_daily_checkins"
down_revision: Union[str, None] = "2026_05_10_remove_daily_checkins"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_table(inspector, "daily_checkins"):
        op.create_table(
            "daily_checkins",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("streak_day", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("coin_earned", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "date", name="uq_daily_checkins_user_date"),
        )
    if not _has_index(inspector, "daily_checkins", "ix_daily_checkins_user_date"):
        op.create_index("ix_daily_checkins_user_date", "daily_checkins", ["user_id", "date"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_index(inspector, "daily_checkins", "ix_daily_checkins_user_date"):
        op.drop_index("ix_daily_checkins_user_date", table_name="daily_checkins")
    if _has_table(inspector, "daily_checkins"):
        op.drop_table("daily_checkins")
