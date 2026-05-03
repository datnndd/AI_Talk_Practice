"""lesson audio assets

Revision ID: 2026_05_03_lesson_audio_assets
Revises: 2026_05_02_subscription_plans
Create Date: 2026-05-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2026_05_03_lesson_audio_assets"
down_revision: Union[str, None] = "2026_05_02_subscription_plans"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index.get("name") for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "lesson_audio_assets"):
        op.create_table(
            "lesson_audio_assets",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("source", sa.String(length=20), nullable=False),
            sa.Column("text", sa.Text(), nullable=True),
            sa.Column("voice", sa.String(length=100), nullable=True),
            sa.Column("language", sa.String(length=20), nullable=True),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("url", sa.String(length=1000), nullable=False),
            sa.Column("content_type", sa.String(length=100), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.CheckConstraint("source IN ('tts','upload')", name="ck_lesson_audio_assets_source"),
            sa.CheckConstraint("size_bytes > 0", name="ck_lesson_audio_assets_size_positive"),
        )
    if not _has_index(inspector, "lesson_audio_assets", "ix_lesson_audio_assets_lesson_created"):
        op.create_index(
            "ix_lesson_audio_assets_lesson_created",
            "lesson_audio_assets",
            ["lesson_id", "created_at"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "lesson_audio_assets", "ix_lesson_audio_assets_lesson_created"):
        op.drop_index("ix_lesson_audio_assets_lesson_created", table_name="lesson_audio_assets")
    if _has_table(inspector, "lesson_audio_assets"):
        op.drop_table("lesson_audio_assets")
