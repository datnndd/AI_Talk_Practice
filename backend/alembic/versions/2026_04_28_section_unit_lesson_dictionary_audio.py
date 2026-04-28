"""section unit lesson dictionary audio

Revision ID: 2026_04_28_section_unit_lesson_dictionary_audio
Revises: 2026_04_27_add_scenario_is_pro
Create Date: 2026-04-28 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_04_28_section_unit_lesson_dictionary_audio"
down_revision: Union[str, None] = "2026_04_27_add_scenario_is_pro"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_check_constraint(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return constraint_name in {constraint["name"] for constraint in inspector.get_check_constraints(table_name)}


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _rename_table(inspector: sa.Inspector, old_name: str, new_name: str) -> None:
    if _has_table(inspector, old_name) and not _has_table(inspector, new_name):
        op.rename_table(old_name, new_name)


def _rename_column(inspector: sa.Inspector, table_name: str, old_name: str, new_name: str) -> None:
    if _has_column(inspector, table_name, old_name) and not _has_column(inspector, table_name, new_name):
        op.alter_column(table_name, old_name, new_column_name=new_name)


def _drop_check_constraint_if_exists(inspector: sa.Inspector, name: str, table_name: str) -> None:
    if _has_check_constraint(inspector, table_name, name):
        op.drop_constraint(name, table_name, type_="check")


def _drop_index_if_exists(inspector: sa.Inspector, name: str, table_name: str) -> None:
    if _has_index(inspector, table_name, name):
        op.drop_index(name, table_name=table_name)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _rename_table(inspector, "learning_levels", "learning_sections")
    inspector = sa.inspect(bind)
    if _has_table(inspector, "learning_sections") and not _has_column(inspector, "learning_sections", "cefr_level"):
        op.add_column("learning_sections", sa.Column("cefr_level", sa.String(length=10), nullable=True))

    _rename_table(inspector, "lessons", "units")
    inspector = sa.inspect(bind)
    _rename_column(inspector, "units", "level_id", "section_id")

    _rename_table(inspector, "lesson_exercises", "lessons")
    inspector = sa.inspect(bind)
    _rename_column(inspector, "lessons", "lesson_id", "unit_id")
    if _has_table(inspector, "lessons"):
        _drop_check_constraint_if_exists(inspector, "ck_lesson_exercises_type", "lessons")
        inspector = sa.inspect(bind)
        _drop_check_constraint_if_exists(inspector, "ck_lessons_type", "lessons")
        op.create_check_constraint(
            "ck_lessons_type",
            "lessons",
            "type IN ('vocab_pronunciation','cloze_dictation','sentence_pronunciation','interactive_conversation','word_audio_choice')",
        )

    _rename_table(inspector, "user_lesson_progress", "user_unit_progress")
    inspector = sa.inspect(bind)
    _rename_column(inspector, "user_unit_progress", "lesson_id", "unit_id")

    _rename_table(inspector, "user_exercise_progress", "user_lesson_progress")
    inspector = sa.inspect(bind)
    _rename_column(inspector, "user_lesson_progress", "exercise_id", "lesson_id")

    _rename_table(inspector, "exercise_attempts", "lesson_attempts")
    inspector = sa.inspect(bind)
    _rename_column(inspector, "lesson_attempts", "exercise_id", "lesson_id")

    if _has_table(inspector, "dictionary_terms"):
        _drop_index_if_exists(inspector, "ix_dictionary_terms_word", "dictionary_terms")
        op.drop_table("dictionary_terms")

    inspector = sa.inspect(bind)
    if not _has_table(inspector, "dictionary_audio_cache"):
        op.create_table(
            "dictionary_audio_cache",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("normalized_word", sa.String(length=200), nullable=False),
            sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
            sa.Column("source", sa.String(length=100), nullable=False, server_default="dict.minhqnd.com"),
            sa.Column("source_url", sa.String(length=1000), nullable=False),
            sa.Column("content_type", sa.String(length=100), nullable=False, server_default="audio/wav"),
            sa.Column("audio_bytes", sa.LargeBinary(), nullable=False),
            sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("normalized_word", "language", name="uq_dictionary_audio_cache_word_language"),
        )
        op.create_index("ix_dictionary_audio_cache_word", "dictionary_audio_cache", ["normalized_word"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _has_table(inspector, "dictionary_audio_cache"):
        op.drop_index("ix_dictionary_audio_cache_word", table_name="dictionary_audio_cache")
        op.drop_table("dictionary_audio_cache")

    inspector = sa.inspect(bind)
    _rename_column(inspector, "lesson_attempts", "lesson_id", "exercise_id")
    _rename_table(inspector, "lesson_attempts", "exercise_attempts")

    inspector = sa.inspect(bind)
    _rename_column(inspector, "user_lesson_progress", "lesson_id", "exercise_id")
    _rename_table(inspector, "user_lesson_progress", "user_exercise_progress")

    inspector = sa.inspect(bind)
    _rename_column(inspector, "user_unit_progress", "unit_id", "lesson_id")
    _rename_table(inspector, "user_unit_progress", "user_lesson_progress")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "lessons"):
        _drop_check_constraint_if_exists(inspector, "ck_lessons_type", "lessons")
        op.create_check_constraint(
            "ck_lesson_exercises_type",
            "lessons",
            "type IN ('vocab_pronunciation','cloze_dictation','sentence_pronunciation','interactive_conversation')",
        )
    _rename_column(inspector, "lessons", "unit_id", "lesson_id")
    _rename_table(inspector, "lessons", "lesson_exercises")

    inspector = sa.inspect(bind)
    _rename_column(inspector, "units", "section_id", "level_id")
    _rename_table(inspector, "units", "lessons")

    inspector = sa.inspect(bind)
    if _has_column(inspector, "learning_sections", "cefr_level"):
        op.drop_column("learning_sections", "cefr_level")
    _rename_table(inspector, "learning_sections", "learning_levels")
