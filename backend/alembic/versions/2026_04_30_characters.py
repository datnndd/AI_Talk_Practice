"""Add characters for Live2D avatars and TTS voices

Revision ID: 2026_04_30_characters
Revises: 2026_04_28_merge_user_language_and_scenario_image
Create Date: 2026-04-30 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "2026_04_30_characters"
down_revision: Union[str, None] = "2026_04_28_merge_user_language_and_scenario_image"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_MODEL_URL = (
    "https://rgpmptospjqospitmcqw.supabase.co/storage/v1/object/public/"
    "live2d-models/ai-tutor/pachirisu%20anime%20girl%20-%20top%20half.model3.json"
)
DEFAULT_CORE_URL = (
    "https://rgpmptospjqospitmcqw.supabase.co/storage/v1/object/public/"
    "live2d-models/live2dcubismcore.min.js"
)


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_fk(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return constraint_name in {fk.get("name") for fk in inspector.get_foreign_keys(table_name)}


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index.get("name") for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "characters"):
        op.create_table(
            "characters",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("model_url", sa.String(length=1000), nullable=False),
            sa.Column("core_url", sa.String(length=1000), nullable=False),
            sa.Column("thumbnail_url", sa.String(length=1000), nullable=True),
            sa.Column("tts_voice", sa.String(length=100), nullable=False, server_default="Cherry"),
            sa.Column("tts_language", sa.String(length=20), nullable=False, server_default="en"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    inspector = sa.inspect(bind)
    if not _has_index(inspector, "characters", "ix_characters_active"):
        op.create_index(
            "ix_characters_active",
            "characters",
            ["is_active"],
            postgresql_where=sa.text("deleted_at IS NULL"),
        )
    if not _has_index(inspector, "characters", "ix_characters_sort_order"):
        op.create_index("ix_characters_sort_order", "characters", ["sort_order", "id"])

    if not _has_column(inspector, "scenarios", "character_id"):
        op.add_column("scenarios", sa.Column("character_id", sa.Integer(), nullable=True))
    if not _has_column(inspector, "sessions", "character_id"):
        op.add_column("sessions", sa.Column("character_id", sa.Integer(), nullable=True))

    inspector = sa.inspect(bind)
    if not _has_fk(inspector, "scenarios", "fk_scenarios_character_id_characters"):
        op.create_foreign_key(
            "fk_scenarios_character_id_characters",
            "scenarios",
            "characters",
            ["character_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not _has_fk(inspector, "sessions", "fk_sessions_character_id_characters"):
        op.create_foreign_key(
            "fk_sessions_character_id_characters",
            "sessions",
            "characters",
            ["character_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not _has_index(inspector, "sessions", "ix_sessions_character_id"):
        op.create_index("ix_sessions_character_id", "sessions", ["character_id"])

    characters = sa.table(
        "characters",
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("model_url", sa.String),
        sa.column("core_url", sa.String),
        sa.column("tts_voice", sa.String),
        sa.column("tts_language", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
        sa.column("metadata", postgresql.JSONB),
    )
    default_character_id = bind.execute(
        sa.text("SELECT id FROM characters WHERE model_url = :model_url AND deleted_at IS NULL LIMIT 1"),
        {"model_url": DEFAULT_MODEL_URL},
    ).scalar()
    if default_character_id is None:
        bind.execute(
            characters.insert().values(
                name="AI Tutor",
                description="Default Live2D AI speaking partner.",
                model_url=DEFAULT_MODEL_URL,
                core_url=DEFAULT_CORE_URL,
                tts_voice="Cherry",
                tts_language="en",
                is_active=True,
                sort_order=0,
                metadata={},
            )
        )
        default_character_id = bind.execute(
            sa.text("SELECT id FROM characters WHERE model_url = :model_url AND deleted_at IS NULL LIMIT 1"),
            {"model_url": DEFAULT_MODEL_URL},
        ).scalar()

    if default_character_id is not None:
        bind.execute(
            sa.text("UPDATE scenarios SET character_id = :character_id WHERE character_id IS NULL"),
            {"character_id": default_character_id},
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "sessions", "ix_sessions_character_id"):
        op.drop_index("ix_sessions_character_id", table_name="sessions")
    if _has_fk(inspector, "sessions", "fk_sessions_character_id_characters"):
        op.drop_constraint("fk_sessions_character_id_characters", "sessions", type_="foreignkey")
    if _has_fk(inspector, "scenarios", "fk_scenarios_character_id_characters"):
        op.drop_constraint("fk_scenarios_character_id_characters", "scenarios", type_="foreignkey")
    if _has_column(inspector, "sessions", "character_id"):
        op.drop_column("sessions", "character_id")
    if _has_column(inspector, "scenarios", "character_id"):
        op.drop_column("scenarios", "character_id")
    if _has_table(inspector, "characters"):
        op.drop_table("characters")
