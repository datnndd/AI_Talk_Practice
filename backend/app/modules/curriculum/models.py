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
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models.user import User


class LearningSection(Base, TimestampMixin):
    __tablename__ = "learning_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    cefr_level: Mapped[Optional[str]] = mapped_column(String(10))
    description: Mapped[Optional[str]] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    units: Mapped[list["Unit"]] = relationship(
        "Unit",
        back_populates="section",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Unit.order_index",
    )

    __table_args__ = (
        Index("ix_learning_sections_active_order", "is_active", "order_index"),
        CheckConstraint("order_index >= 0", name="ck_learning_sections_order_nonnegative"),
    )


class Unit(Base, TimestampMixin):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("learning_sections.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=50, server_default="50")
    coin_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    section: Mapped["LearningSection"] = relationship("LearningSection", back_populates="units", lazy="select")
    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson",
        back_populates="unit",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Lesson.order_index",
    )
    progress: Mapped[list["UserUnitProgress"]] = relationship(
        "UserUnitProgress",
        back_populates="unit",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("section_id", "order_index", name="uq_units_section_order"),
        Index("ix_units_section_active_order", "section_id", "is_active", "order_index"),
        CheckConstraint("order_index >= 0", name="ck_units_order_nonnegative"),
    )


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    content: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default="{}")
    pass_score: Mapped[float] = mapped_column(Float, nullable=False, server_default="80")
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    unit: Mapped["Unit"] = relationship("Unit", back_populates="lessons", lazy="select")
    progress: Mapped[list["UserLessonProgress"]] = relationship(
        "UserLessonProgress",
        back_populates="lesson",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    attempts: Mapped[list["LessonAttempt"]] = relationship(
        "LessonAttempt",
        back_populates="lesson",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("unit_id", "order_index", name="uq_lessons_unit_order"),
        Index("ix_lessons_unit_active_order", "unit_id", "is_active", "order_index"),
        CheckConstraint(
            "type IN ('vocab_pronunciation','cloze_dictation','sentence_pronunciation','interactive_conversation','word_audio_choice')",
            name="ck_lessons_type",
        ),
        CheckConstraint("order_index >= 0", name="ck_lessons_order_nonnegative"),
        CheckConstraint("pass_score >= 0 AND pass_score <= 100", name="ck_lessons_pass_score"),
    )


class UserUnitProgress(Base, TimestampMixin):
    __tablename__ = "user_unit_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="not_started")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    best_score: Mapped[Optional[float]] = mapped_column(Float)

    unit: Mapped["Unit"] = relationship("Unit", back_populates="progress", lazy="select")
    user: Mapped["User"] = relationship("User", lazy="select")

    __table_args__ = (
        UniqueConstraint("user_id", "unit_id", name="uq_user_unit_progress_user_unit"),
        Index("ix_user_unit_progress_user_status", "user_id", "status"),
        CheckConstraint("status IN ('not_started','in_progress','completed')", name="ck_user_unit_progress_status"),
    )


class UserLessonProgress(Base, TimestampMixin):
    __tablename__ = "user_lesson_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="not_started")
    best_score: Mapped[Optional[float]] = mapped_column(Float)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    state: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="{}")

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="progress", lazy="select")
    user: Mapped["User"] = relationship("User", lazy="select")

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress_user_lesson"),
        Index("ix_user_lesson_progress_user_status", "user_id", "status"),
        CheckConstraint("status IN ('not_started','in_progress','completed')", name="ck_user_lesson_progress_status"),
    )


class LessonAttempt(Base, TimestampMixin):
    __tablename__ = "lesson_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    answer: Mapped[Optional[Any]] = mapped_column(JSONB)
    audio_url: Mapped[Optional[str]] = mapped_column(String(1000))
    score: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    attempt_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSONB, server_default="{}")

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="attempts", lazy="select")
    user: Mapped["User"] = relationship("User", lazy="select")

    __table_args__ = (
        Index("ix_lesson_attempts_user_lesson_created", "user_id", "lesson_id", "created_at"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_lesson_attempts_score"),
    )


class DictionaryAudioCache(Base, TimestampMixin):
    __tablename__ = "dictionary_audio_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    normalized_word: Mapped[str] = mapped_column(String(200), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    source: Mapped[str] = mapped_column(String(100), nullable=False, server_default="dict.minhqnd.com")
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, server_default="audio/wav")
    audio_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("normalized_word", "language", name="uq_dictionary_audio_cache_word_language"),
        Index("ix_dictionary_audio_cache_word", "normalized_word"),
    )
