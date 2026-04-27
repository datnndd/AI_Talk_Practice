from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models.user import User


class LearningLevel(Base, TimestampMixin):
    __tablename__ = "learning_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson",
        back_populates="level",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Lesson.order_index",
    )

    __table_args__ = (
        Index("ix_learning_levels_active_order", "is_active", "order_index"),
        CheckConstraint("order_index >= 0", name="ck_learning_levels_order_nonnegative"),
    )


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("learning_levels.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=50, server_default="50")
    coin_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    level: Mapped["LearningLevel"] = relationship("LearningLevel", back_populates="lessons", lazy="select")
    exercises: Mapped[list["LessonExercise"]] = relationship(
        "LessonExercise",
        back_populates="lesson",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LessonExercise.order_index",
    )
    progress: Mapped[list["UserLessonProgress"]] = relationship(
        "UserLessonProgress",
        back_populates="lesson",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("level_id", "order_index", name="uq_lessons_level_order"),
        Index("ix_lessons_level_active_order", "level_id", "is_active", "order_index"),
        CheckConstraint("order_index >= 0", name="ck_lessons_order_nonnegative"),
    )


class LessonExercise(Base, TimestampMixin):
    __tablename__ = "lesson_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    content: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default="{}")
    pass_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="80")
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="exercises", lazy="select")
    progress: Mapped[list["UserExerciseProgress"]] = relationship(
        "UserExerciseProgress",
        back_populates="exercise",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    attempts: Mapped[list["ExerciseAttempt"]] = relationship(
        "ExerciseAttempt",
        back_populates="exercise",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("lesson_id", "order_index", name="uq_lesson_exercises_lesson_order"),
        Index("ix_lesson_exercises_lesson_active_order", "lesson_id", "is_active", "order_index"),
        CheckConstraint(
            "type IN ('vocab_pronunciation','cloze_dictation','sentence_pronunciation','interactive_conversation')",
            name="ck_lesson_exercises_type",
        ),
        CheckConstraint("order_index >= 0", name="ck_lesson_exercises_order_nonnegative"),
        CheckConstraint("pass_score >= 0 AND pass_score <= 100", name="ck_lesson_exercises_pass_score"),
    )


class UserLessonProgress(Base, TimestampMixin):
    __tablename__ = "user_lesson_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="not_started")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    best_score: Mapped[Optional[float]] = mapped_column(Float)

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="progress", lazy="select")
    user: Mapped["User"] = relationship("User", lazy="select")

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress_user_lesson"),
        Index("ix_user_lesson_progress_user_status", "user_id", "status"),
        CheckConstraint("status IN ('not_started','in_progress','completed')", name="ck_user_lesson_progress_status"),
    )


class UserExerciseProgress(Base, TimestampMixin):
    __tablename__ = "user_exercise_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lesson_exercises.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="not_started")
    best_score: Mapped[Optional[float]] = mapped_column(Float)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    state: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="{}")

    exercise: Mapped["LessonExercise"] = relationship("LessonExercise", back_populates="progress", lazy="select")
    user: Mapped["User"] = relationship("User", lazy="select")

    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="uq_user_exercise_progress_user_exercise"),
        Index("ix_user_exercise_progress_user_status", "user_id", "status"),
        CheckConstraint("status IN ('not_started','in_progress','completed')", name="ck_user_exercise_progress_status"),
    )


class ExerciseAttempt(Base, TimestampMixin):
    __tablename__ = "exercise_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lesson_exercises.id", ondelete="CASCADE"), nullable=False
    )
    answer: Mapped[Optional[Any]] = mapped_column(JSONB)
    audio_url: Mapped[Optional[str]] = mapped_column(String(1000))
    score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    attempt_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSONB, server_default="{}")

    exercise: Mapped["LessonExercise"] = relationship("LessonExercise", back_populates="attempts", lazy="select")
    user: Mapped["User"] = relationship("User", lazy="select")

    __table_args__ = (
        Index("ix_exercise_attempts_user_exercise_created", "user_id", "exercise_id", "created_at"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_exercise_attempts_score"),
    )


class DictionaryTerm(Base, TimestampMixin):
    __tablename__ = "dictionary_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    normalized_word: Mapped[str] = mapped_column(String(200), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    meaning_vi: Mapped[Optional[str]] = mapped_column(Text)
    ipa: Mapped[Optional[str]] = mapped_column(String(200))
    audio_path: Mapped[Optional[str]] = mapped_column(String(1000))
    source_metadata: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="{}")

    __table_args__ = (
        UniqueConstraint("normalized_word", "language", name="uq_dictionary_terms_word_language"),
        Index("ix_dictionary_terms_word", "normalized_word"),
    )
