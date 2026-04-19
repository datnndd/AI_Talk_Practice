"""simple gamification

Revision ID: 2026_04_19_simple_gamification
Revises: 2026_04_19_remove_scenario_variations
Create Date: 2026-04-19 23:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_19_simple_gamification"
down_revision: Union[str, None] = "2026_04_19_remove_scenario_variations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {
        "last_completed_lesson_date": sa.Column("last_completed_lesson_date", sa.Date(), nullable=True),
        "total_xp": sa.Column("total_xp", sa.Integer(), nullable=False, server_default="0"),
        "daily_xp_goal": sa.Column("daily_xp_goal", sa.Integer(), nullable=False, server_default="50"),
        "gem_balance": sa.Column("gem_balance", sa.Integer(), nullable=False, server_default="0"),
        "heart_balance": sa.Column("heart_balance", sa.Integer(), nullable=False, server_default="5"),
        "heart_max": sa.Column("heart_max", sa.Integer(), nullable=False, server_default="5"),
        "last_heart_refill_at": sa.Column("last_heart_refill_at", sa.DateTime(timezone=True), nullable=True),
        "total_lessons_completed": sa.Column("total_lessons_completed", sa.Integer(), nullable=False, server_default="0"),
        "total_speaking_lessons_completed": sa.Column(
            "total_speaking_lessons_completed", sa.Integer(), nullable=False, server_default="0"
        ),
        "total_vocabulary_lessons_completed": sa.Column(
            "total_vocabulary_lessons_completed", sa.Integer(), nullable=False, server_default="0"
        ),
        "perfect_score_count": sa.Column("perfect_score_count", sa.Integer(), nullable=False, server_default="0"),
        "daily_goal_streak": sa.Column("daily_goal_streak", sa.Integer(), nullable=False, server_default="0"),
        "last_daily_goal_date": sa.Column("last_daily_goal_date", sa.Date(), nullable=True),
    }

    with op.batch_alter_table("users") as batch_op:
        for column_name, column in user_columns.items():
            if not _has_column(inspector, "users", column_name):
                batch_op.add_column(column)

    if not _has_table(inspector, "achievements"):
        op.create_table(
            "achievements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=50), nullable=False, unique=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=False),
            sa.Column("icon_url", sa.String(length=500), nullable=True),
            sa.Column("gem_reward", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("condition", sa.JSON(), nullable=False),
        )
    elif not _has_column(inspector, "achievements", "gem_reward"):
        with op.batch_alter_table("achievements") as batch_op:
            batch_op.add_column(sa.Column("gem_reward", sa.Integer(), nullable=False, server_default="0"))

    if not _has_table(inspector, "daily_stats"):
        op.create_table(
            "daily_stats",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("minutes_practiced", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("lessons_completed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("speaking_lessons_completed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("vocabulary_lessons_completed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("daily_goal_met", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("avg_score", sa.Float(), nullable=True),
            sa.Column("recordings_count", sa.Integer(), nullable=False, server_default="0"),
            sa.UniqueConstraint("user_id", "date"),
        )
    else:
        daily_stat_columns = {
            "xp_earned": sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
            "lessons_completed": sa.Column("lessons_completed", sa.Integer(), nullable=False, server_default="0"),
            "speaking_lessons_completed": sa.Column("speaking_lessons_completed", sa.Integer(), nullable=False, server_default="0"),
            "vocabulary_lessons_completed": sa.Column(
                "vocabulary_lessons_completed", sa.Integer(), nullable=False, server_default="0"
            ),
            "daily_goal_met": sa.Column("daily_goal_met", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        }
        with op.batch_alter_table("daily_stats") as batch_op:
            for column_name, column in daily_stat_columns.items():
                if not _has_column(inspector, "daily_stats", column_name):
                    batch_op.add_column(column)

    if not _has_table(inspector, "user_achievements"):
        op.create_table(
            "user_achievements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("achievement_id", sa.Integer(), sa.ForeignKey("achievements.id"), nullable=True),
            sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "achievement_id"),
        )

    if not _has_table(inspector, "gem_transactions"):
        op.create_table(
            "gem_transactions",
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
        op.create_index("ix_gem_transactions_user_created", "gem_transactions", ["user_id", "created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "gem_transactions"):
        op.drop_index("ix_gem_transactions_user_created", table_name="gem_transactions")
        op.drop_table("gem_transactions")

    if _has_table(inspector, "daily_stats"):
        with op.batch_alter_table("daily_stats") as batch_op:
            for column_name in (
                "daily_goal_met",
                "vocabulary_lessons_completed",
                "speaking_lessons_completed",
                "lessons_completed",
                "xp_earned",
            ):
                if _has_column(inspector, "daily_stats", column_name):
                    batch_op.drop_column(column_name)

    if _has_column(inspector, "achievements", "gem_reward"):
        with op.batch_alter_table("achievements") as batch_op:
            batch_op.drop_column("gem_reward")

    with op.batch_alter_table("users") as batch_op:
        for column_name in (
            "last_daily_goal_date",
            "daily_goal_streak",
            "perfect_score_count",
            "total_vocabulary_lessons_completed",
            "total_speaking_lessons_completed",
            "total_lessons_completed",
            "last_heart_refill_at",
            "heart_max",
            "heart_balance",
            "gem_balance",
            "daily_xp_goal",
            "total_xp",
            "last_completed_lesson_date",
        ):
            if _has_column(inspector, "users", column_name):
                batch_op.drop_column(column_name)
