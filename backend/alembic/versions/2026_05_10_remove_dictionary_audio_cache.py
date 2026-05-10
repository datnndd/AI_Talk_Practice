"""remove dictionary audio cache

Revision ID: 2026_05_10_remove_dictionary_audio_cache
Revises: 2026_05_10_drop_lesson_required
Create Date: 2026-05-10 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "2026_05_10_remove_dictionary_audio_cache"
down_revision: Union[str, None] = "2026_05_10_drop_lesson_required"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table(sa.inspect(bind), "dictionary_audio_cache"):
        op.drop_table("dictionary_audio_cache")


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(sa.inspect(bind), "dictionary_audio_cache"):
        return
    json_type = postgresql.JSONB() if bind.dialect.name == "postgresql" else sa.JSON()
    op.create_table(
        "dictionary_audio_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("normalized_word", sa.String(length=200), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("source", sa.String(length=100), nullable=False, server_default="dict.minhqnd.com"),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=False, server_default="audio/wav"),
        sa.Column("audio_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("normalized_word", "language", name="uq_dictionary_audio_cache_word_language"),
    )
    op.create_index("ix_dictionary_audio_cache_word", "dictionary_audio_cache", ["normalized_word"])
