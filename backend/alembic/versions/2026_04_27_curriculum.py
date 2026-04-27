"""curriculum

Revision ID: 2026_04_27_curriculum
Revises: 2026_04_20_remove_scenario_start_flags
Create Date: 2026-04-27 06:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_04_27_curriculum"
down_revision: Union[str, None] = "2026_04_20_remove_scenario_start_flags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "learning_levels"):
        op.create_table(
            "learning_levels",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=50), nullable=False, unique=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("order_index >= 0", name="ck_learning_levels_order_nonnegative"),
        )
        op.create_index("ix_learning_levels_active_order", "learning_levels", ["is_active", "order_index"])

    if not _has_table(inspector, "lessons"):
        op.create_table(
            "lessons",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("level_id", sa.Integer(), sa.ForeignKey("learning_levels.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("estimated_minutes", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("order_index >= 0", name="ck_lessons_order_nonnegative"),
            sa.UniqueConstraint("level_id", "order_index", name="uq_lessons_level_order"),
        )
        op.create_index("ix_lessons_level_active_order", "lessons", ["level_id", "is_active", "order_index"])

    if not _has_table(inspector, "lesson_exercises"):
        op.create_table(
            "lesson_exercises",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", sa.String(length=40), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("content", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("pass_score", sa.Float(), nullable=False, server_default="80"),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint(
                "type IN ('vocab_pronunciation','cloze_dictation','sentence_pronunciation','interactive_conversation')",
                name="ck_lesson_exercises_type",
            ),
            sa.CheckConstraint("order_index >= 0", name="ck_lesson_exercises_order_nonnegative"),
            sa.CheckConstraint("pass_score >= 0 AND pass_score <= 100", name="ck_lesson_exercises_pass_score"),
            sa.UniqueConstraint("lesson_id", "order_index", name="uq_lesson_exercises_lesson_order"),
        )
        op.create_index(
            "ix_lesson_exercises_lesson_active_order",
            "lesson_exercises",
            ["lesson_id", "is_active", "order_index"],
        )

    if not _has_table(inspector, "user_lesson_progress"):
        op.create_table(
            "user_lesson_progress",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="not_started"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("best_score", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("status IN ('not_started','in_progress','completed')", name="ck_user_lesson_progress_status"),
            sa.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress_user_lesson"),
        )
        op.create_index("ix_user_lesson_progress_user_status", "user_lesson_progress", ["user_id", "status"])

    if not _has_table(inspector, "user_exercise_progress"):
        op.create_table(
            "user_exercise_progress",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("lesson_exercises.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="not_started"),
            sa.Column("best_score", sa.Float(), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("state", sa.JSON(), nullable=True, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("status IN ('not_started','in_progress','completed')", name="ck_user_exercise_progress_status"),
            sa.UniqueConstraint("user_id", "exercise_id", name="uq_user_exercise_progress_user_exercise"),
        )
        op.create_index("ix_user_exercise_progress_user_status", "user_exercise_progress", ["user_id", "status"])

    if not _has_table(inspector, "exercise_attempts"):
        op.create_table(
            "exercise_attempts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("lesson_exercises.id", ondelete="CASCADE"), nullable=False),
            sa.Column("answer", sa.JSON(), nullable=True),
            sa.Column("audio_url", sa.String(length=1000), nullable=True),
            sa.Column("score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("metadata", sa.JSON(), nullable=True, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_exercise_attempts_score"),
        )
        op.create_index(
            "ix_exercise_attempts_user_exercise_created",
            "exercise_attempts",
            ["user_id", "exercise_id", "created_at"],
        )

    if not _has_table(inspector, "dictionary_terms"):
        op.create_table(
            "dictionary_terms",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("normalized_word", sa.String(length=200), nullable=False),
            sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
            sa.Column("meaning_vi", sa.Text(), nullable=True),
            sa.Column("ipa", sa.String(length=200), nullable=True),
            sa.Column("audio_path", sa.String(length=1000), nullable=True),
            sa.Column("source_metadata", sa.JSON(), nullable=True, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("normalized_word", "language", name="uq_dictionary_terms_word_language"),
        )
        op.create_index("ix_dictionary_terms_word", "dictionary_terms", ["normalized_word"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for index_name, table_name in (
        ("ix_dictionary_terms_word", "dictionary_terms"),
        ("ix_exercise_attempts_user_exercise_created", "exercise_attempts"),
        ("ix_user_exercise_progress_user_status", "user_exercise_progress"),
        ("ix_user_lesson_progress_user_status", "user_lesson_progress"),
        ("ix_lesson_exercises_lesson_active_order", "lesson_exercises"),
        ("ix_lessons_level_active_order", "lessons"),
        ("ix_learning_levels_active_order", "learning_levels"),
    ):
        if _has_table(inspector, table_name):
            op.drop_index(index_name, table_name=table_name)

    for table_name in (
        "dictionary_terms",
        "exercise_attempts",
        "user_exercise_progress",
        "user_lesson_progress",
        "lesson_exercises",
        "lessons",
        "learning_levels",
    ):
        if _has_table(inspector, table_name):
            op.drop_table(table_name)
