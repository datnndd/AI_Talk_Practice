"""admin panel gamification support

Revision ID: 2026_04_19_admin_panel_gamification
Revises: 2026_04_19_simple_gamification
Create Date: 2026-04-19 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_19_admin_panel_gamification"
down_revision: Union[str, None] = "2026_04_19_simple_gamification"
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

    if not _has_table(inspector, "gamification_settings"):
        op.create_table(
            "gamification_settings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("key", sa.String(length=80), nullable=False, unique=True),
            sa.Column("value", sa.JSON(), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    if not _has_table(inspector, "admin_audit_logs"):
        op.create_table(
            "admin_audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("entity_type", sa.String(length=80), nullable=False),
            sa.Column("entity_id", sa.String(length=80), nullable=True),
            sa.Column("target_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("before", sa.JSON(), nullable=True),
            sa.Column("after", sa.JSON(), nullable=True),
            sa.Column("reason", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    if not _has_index(inspector, "admin_audit_logs", "ix_admin_audit_logs_created_at"):
        op.create_index("ix_admin_audit_logs_created_at", "admin_audit_logs", ["created_at"])
    if not _has_index(inspector, "admin_audit_logs", "ix_admin_audit_logs_actor_created"):
        op.create_index("ix_admin_audit_logs_actor_created", "admin_audit_logs", ["actor_user_id", "created_at"])

    if not _has_table(inspector, "notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("sender_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("recipient_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("audience", sa.String(length=20), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    if not _has_index(inspector, "notifications", "ix_notifications_recipient_created"):
        op.create_index("ix_notifications_recipient_created", "notifications", ["recipient_user_id", "created_at"])

    if not _has_table(inspector, "notification_reads"):
        op.create_table(
            "notification_reads",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("notification_id", sa.Integer(), sa.ForeignKey("notifications.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("notification_id", "user_id"),
        )
    if not _has_index(inspector, "notification_reads", "ix_notification_reads_user_notification"):
        op.create_index(
            "ix_notification_reads_user_notification",
            "notification_reads",
            ["user_id", "notification_id"],
        )

    if _has_table(inspector, "daily_stats") and not _has_index(inspector, "daily_stats", "ix_daily_stats_date"):
        op.create_index("ix_daily_stats_date", "daily_stats", ["date"])

    if _has_table(inspector, "sessions") and not _has_index(inspector, "sessions", "ix_sessions_started_at"):
        op.create_index("ix_sessions_started_at", "sessions", ["started_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "sessions", "ix_sessions_started_at"):
        op.drop_index("ix_sessions_started_at", table_name="sessions")
    if _has_index(inspector, "daily_stats", "ix_daily_stats_date"):
        op.drop_index("ix_daily_stats_date", table_name="daily_stats")

    if _has_index(inspector, "notification_reads", "ix_notification_reads_user_notification"):
        op.drop_index("ix_notification_reads_user_notification", table_name="notification_reads")
    if _has_table(inspector, "notification_reads"):
        op.drop_table("notification_reads")

    if _has_index(inspector, "notifications", "ix_notifications_recipient_created"):
        op.drop_index("ix_notifications_recipient_created", table_name="notifications")
    if _has_table(inspector, "notifications"):
        op.drop_table("notifications")

    if _has_index(inspector, "admin_audit_logs", "ix_admin_audit_logs_actor_created"):
        op.drop_index("ix_admin_audit_logs_actor_created", table_name="admin_audit_logs")
    if _has_index(inspector, "admin_audit_logs", "ix_admin_audit_logs_created_at"):
        op.drop_index("ix_admin_audit_logs_created_at", table_name="admin_audit_logs")
    if _has_table(inspector, "admin_audit_logs"):
        op.drop_table("admin_audit_logs")

    if _has_table(inspector, "gamification_settings"):
        op.drop_table("gamification_settings")

