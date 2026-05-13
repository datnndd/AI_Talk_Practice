"""Replace corrections with message realtime feedbacks

Revision ID: 2026_05_13_message_realtime_feedbacks
Revises: 2026_05_12_remove_scenario_ai_system_prompt
Create Date: 2026-05-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "2026_05_13_message_realtime_feedbacks"
down_revision: Union[str, None] = "2026_05_12_remove_scenario_ai_system_prompt"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = inspector.get_table_names()

    if "message_realtime_feedbacks" not in tables:
        op.create_table(
            "message_realtime_feedbacks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("message_id", sa.Integer(), nullable=False),
            sa.Column("is_good", sa.Boolean(), nullable=False),
            sa.Column("better_answer", sa.Text(), nullable=True),
            sa.Column("raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("message_id", name="uq_message_realtime_feedbacks_message_id"),
        )
        op.create_index(
            "ix_message_realtime_feedbacks_message_id",
            "message_realtime_feedbacks",
            ["message_id"],
        )

    if "corrections" in tables:
        op.drop_table("corrections")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = inspector.get_table_names()

    if "corrections" not in tables:
        op.create_table(
            "corrections",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("message_id", sa.Integer(), nullable=False),
            sa.Column("original_text", sa.Text(), nullable=False),
            sa.Column("corrected_text", sa.Text(), nullable=False),
            sa.Column("explanation", sa.Text(), nullable=False),
            sa.Column("error_type", sa.String(length=30), nullable=False),
            sa.Column("severity", sa.String(length=10), server_default="medium", nullable=False),
            sa.Column("position_start", sa.SmallInteger(), nullable=True),
            sa.Column("position_end", sa.SmallInteger(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint(
                "error_type IN ('grammar','vocabulary','naturalness','pronunciation','register')",
                name="ck_corrections_error_type",
            ),
            sa.CheckConstraint("severity IN ('low','medium','high')", name="ck_corrections_severity"),
            sa.CheckConstraint(
                "(position_start IS NULL AND position_end IS NULL) OR "
                "(position_start IS NOT NULL AND position_end IS NOT NULL AND position_end >= position_start)",
                name="ck_corrections_position",
            ),
        )
        op.create_index("ix_corrections_message_id", "corrections", ["message_id"])
        op.create_index("ix_corrections_error_type", "corrections", ["error_type"])

    if "message_realtime_feedbacks" in tables:
        op.drop_index("ix_message_realtime_feedbacks_message_id", table_name="message_realtime_feedbacks")
        op.drop_table("message_realtime_feedbacks")
