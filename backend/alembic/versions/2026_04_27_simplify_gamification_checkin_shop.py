"""simplify gamification checkin shop

Revision ID: 2026_04_27_simplify_gamification_checkin_shop
Revises: 2026_04_27_remove_achievements
Create Date: 2026-04-27 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_04_27_simplify_gamification_checkin_shop"
down_revision: Union[str, None] = "2026_04_27_remove_achievements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "users"):
        with op.batch_alter_table("users") as batch_op:
            if _has_column(inspector, "users", "gem_balance") and not _has_column(inspector, "users", "coin_balance"):
                batch_op.alter_column("gem_balance", new_column_name="coin_balance")
            elif not _has_column(inspector, "users", "coin_balance"):
                batch_op.add_column(sa.Column("coin_balance", sa.Integer(), nullable=False, server_default="0"))
            for column_name in (
                "current_streak",
                "longest_streak",
                "last_completed_lesson_date",
                "daily_goal_streak",
                "last_daily_goal_date",
                "daily_xp_goal",
                "heart_balance",
                "heart_max",
                "last_heart_refill_at",
            ):
                if _has_column(inspector, "users", column_name):
                    batch_op.drop_column(column_name)

    inspector = sa.inspect(bind)
    if _has_table(inspector, "gem_transactions") and not _has_table(inspector, "coin_transactions"):
        if _has_index(inspector, "gem_transactions", "ix_gem_transactions_user_created"):
            op.drop_index("ix_gem_transactions_user_created", table_name="gem_transactions")
        op.rename_table("gem_transactions", "coin_transactions")
        op.create_index("ix_coin_transactions_user_created", "coin_transactions", ["user_id", "created_at"])
    elif not _has_table(inspector, "coin_transactions"):
        op.create_table(
            "coin_transactions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("type", sa.String(length=40), nullable=False),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("balance_after", sa.Integer(), nullable=False),
            sa.Column("reference_type", sa.String(length=40), nullable=True),
            sa.Column("reference_id", sa.String(length=80), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_coin_transactions_user_created", "coin_transactions", ["user_id", "created_at"])

    inspector = sa.inspect(bind)
    if _has_table(inspector, "lessons"):
        with op.batch_alter_table("lessons") as batch_op:
            if not _has_column(inspector, "lessons", "xp_reward"):
                batch_op.add_column(sa.Column("xp_reward", sa.Integer(), nullable=False, server_default="50"))
            if not _has_column(inspector, "lessons", "coin_reward"):
                batch_op.add_column(sa.Column("coin_reward", sa.Integer(), nullable=False, server_default="0"))

    inspector = sa.inspect(bind)
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
        op.create_index("ix_daily_checkins_user_date", "daily_checkins", ["user_id", "date"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "daily_checkins", "ix_daily_checkins_user_date"):
        op.drop_index("ix_daily_checkins_user_date", table_name="daily_checkins")
    if _has_table(inspector, "daily_checkins"):
        op.drop_table("daily_checkins")

    if _has_table(inspector, "lessons"):
        with op.batch_alter_table("lessons") as batch_op:
            for column_name in ("coin_reward", "xp_reward"):
                if _has_column(inspector, "lessons", column_name):
                    batch_op.drop_column(column_name)

    inspector = sa.inspect(bind)
    if _has_table(inspector, "coin_transactions") and not _has_table(inspector, "gem_transactions"):
        if _has_index(inspector, "coin_transactions", "ix_coin_transactions_user_created"):
            op.drop_index("ix_coin_transactions_user_created", table_name="coin_transactions")
        op.rename_table("coin_transactions", "gem_transactions")
        op.create_index("ix_gem_transactions_user_created", "gem_transactions", ["user_id", "created_at"])

    inspector = sa.inspect(bind)
    if _has_table(inspector, "users"):
        with op.batch_alter_table("users") as batch_op:
            if _has_column(inspector, "users", "coin_balance") and not _has_column(inspector, "users", "gem_balance"):
                batch_op.alter_column("coin_balance", new_column_name="gem_balance")
            if not _has_column(inspector, "users", "daily_xp_goal"):
                batch_op.add_column(sa.Column("daily_xp_goal", sa.Integer(), nullable=False, server_default="50"))
            if not _has_column(inspector, "users", "heart_balance"):
                batch_op.add_column(sa.Column("heart_balance", sa.Integer(), nullable=False, server_default="5"))
            if not _has_column(inspector, "users", "heart_max"):
                batch_op.add_column(sa.Column("heart_max", sa.Integer(), nullable=False, server_default="5"))
            if not _has_column(inspector, "users", "last_heart_refill_at"):
                batch_op.add_column(sa.Column("last_heart_refill_at", sa.DateTime(timezone=True), nullable=True))
            if not _has_column(inspector, "users", "last_daily_goal_date"):
                batch_op.add_column(sa.Column("last_daily_goal_date", sa.Date(), nullable=True))
            if not _has_column(inspector, "users", "daily_goal_streak"):
                batch_op.add_column(sa.Column("daily_goal_streak", sa.Integer(), nullable=False, server_default="0"))
            if not _has_column(inspector, "users", "last_completed_lesson_date"):
                batch_op.add_column(sa.Column("last_completed_lesson_date", sa.Date(), nullable=True))
            if not _has_column(inspector, "users", "longest_streak"):
                batch_op.add_column(sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"))
            if not _has_column(inspector, "users", "current_streak"):
                batch_op.add_column(sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"))
