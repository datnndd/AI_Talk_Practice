"""remove per-message pronunciation scoring

Revision ID: 2026_04_20_remove_message_pronunciation_scoring
Revises: 2026_04_19_admin_panel_gamification
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_20_remove_message_pronunciation_scoring"
down_revision: Union[str, None] = "2026_04_19_admin_panel_gamification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name in ("phoneme_errors", "word_errors", "message_scores"):
        if _has_table(inspector, table_name):
            op.drop_table(table_name)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "message_scores"):
        op.create_table(
            "message_scores",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
            sa.Column("pronunciation_score", sa.Float(), nullable=False),
            sa.Column("fluency_score", sa.Float(), nullable=False),
            sa.Column("grammar_score", sa.Float(), nullable=False),
            sa.Column("vocabulary_score", sa.Float(), nullable=False),
            sa.Column("intonation_score", sa.Float(), nullable=False),
            sa.Column("overall_score", sa.Float(), nullable=False),
            sa.Column("mispronounced_words", sa.JSON(), nullable=True),
            sa.Column("feedback", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("message_id", name="uq_message_scores_message_id"),
            sa.CheckConstraint("pronunciation_score BETWEEN 0 AND 10", name="ck_ms_pronunciation"),
            sa.CheckConstraint("fluency_score BETWEEN 0 AND 10", name="ck_ms_fluency"),
            sa.CheckConstraint("grammar_score BETWEEN 0 AND 10", name="ck_ms_grammar"),
            sa.CheckConstraint("vocabulary_score BETWEEN 0 AND 10", name="ck_ms_vocabulary"),
            sa.CheckConstraint("intonation_score BETWEEN 0 AND 10", name="ck_ms_intonation"),
            sa.CheckConstraint("overall_score BETWEEN 0 AND 10", name="ck_ms_overall"),
        )
    if not _has_index(inspector, "message_scores", "ix_message_scores_message_id"):
        op.create_index("ix_message_scores_message_id", "message_scores", ["message_id"])
    if not _has_index(inspector, "message_scores", "ix_message_scores_overall"):
        op.create_index("ix_message_scores_overall", "message_scores", ["overall_score"])

    if not _has_table(inspector, "word_errors"):
        op.create_table(
            "word_errors",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
            sa.Column("word", sa.String(length=20)),
            sa.Column("error_count", sa.Integer(), server_default="1"),
            sa.Column("avg_severity", sa.Float()),
            sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "word"),
        )

    if not _has_table(inspector, "phoneme_errors"):
        op.create_table(
            "phoneme_errors",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
            sa.Column("phoneme", sa.String(length=20)),
            sa.Column("error_count", sa.Integer(), server_default="1"),
            sa.Column("avg_severity", sa.Float()),
            sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "phoneme"),
        )
