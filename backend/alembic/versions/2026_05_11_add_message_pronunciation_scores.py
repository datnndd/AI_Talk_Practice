"""Add message pronunciation scores

Revision ID: 2026_05_11_add_message_pronunciation_scores
Revises: 2026_05_11_remove_message_audio_metadata
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "2026_05_11_add_message_pronunciation_scores"
down_revision: Union[str, None] = "2026_05_11_remove_message_audio_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "message_pronunciation_scores" in inspector.get_table_names():
        return

    op.create_table(
        "message_pronunciation_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("recognized_text", sa.Text(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("accuracy_score", sa.Float(), nullable=True),
        sa.Column("fluency_score", sa.Float(), nullable=True),
        sa.Column("completeness_score", sa.Float(), nullable=True),
        sa.Column("prosody_score", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("raw_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", name="uq_message_pronunciation_scores_message_id"),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'skipped')", name="ck_mps_status"),
        sa.CheckConstraint("overall_score IS NULL OR overall_score BETWEEN 0 AND 100", name="ck_mps_overall"),
        sa.CheckConstraint("accuracy_score IS NULL OR accuracy_score BETWEEN 0 AND 100", name="ck_mps_accuracy"),
        sa.CheckConstraint("fluency_score IS NULL OR fluency_score BETWEEN 0 AND 100", name="ck_mps_fluency"),
        sa.CheckConstraint("completeness_score IS NULL OR completeness_score BETWEEN 0 AND 100", name="ck_mps_completeness"),
        sa.CheckConstraint("prosody_score IS NULL OR prosody_score BETWEEN 0 AND 100", name="ck_mps_prosody"),
    )
    op.create_index("ix_message_pronunciation_scores_message_id", "message_pronunciation_scores", ["message_id"])
    op.create_index("ix_message_pronunciation_scores_status", "message_pronunciation_scores", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "message_pronunciation_scores" not in inspector.get_table_names():
        return
    op.drop_index("ix_message_pronunciation_scores_status", table_name="message_pronunciation_scores")
    op.drop_index("ix_message_pronunciation_scores_message_id", table_name="message_pronunciation_scores")
    op.drop_table("message_pronunciation_scores")
