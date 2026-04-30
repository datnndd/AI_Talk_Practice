"""Scenario models for reusable speaking-practice templates."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.characters.models.character import Character
    from app.modules.sessions.models.session import Session


class Scenario(Base, TimestampMixin):
    """
    A conversation scenario template.

    Design notes:
    - `ai_system_prompt` is the scenario-specific instruction used at runtime.
    - `tasks` JSONB: learner tasks required to complete the conversation.
    - `tags` JSONB: ["airport", "formal", "beginner-friendly"] — aids recommendation.
    - `estimated_duration` in seconds — used for session time predictions in the UI.
    - Soft-delete via `deleted_at` — never hard-delete published scenarios.
    """

    __tablename__ = "scenarios"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── Content ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    ai_system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    ai_role: Mapped[str] = mapped_column(String(500), nullable=False, server_default="")
    user_role: Mapped[str] = mapped_column(String(500), nullable=False, server_default="")
    # JSONB: ["say your name", "say your age", "say where you are from"]
    tasks: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="[]")

    # ── Classification ────────────────────────────────────────────────────────
    category: Mapped[str] = mapped_column(String(50), nullable=False)     # "travel", "business"
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")
    # JSONB: ["restaurant", "polite", "formal"]
    tags: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="[]")

    # ── Session parameters ────────────────────────────────────────────────────
    estimated_duration: Mapped[Optional[int]] = mapped_column(SmallInteger)  # seconds
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer)  # New: session time limit in minutes
    character_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Admin ─────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="scenario",
        lazy="select",
        passive_deletes=True,
    )
    character: Mapped[Optional["Character"]] = relationship(
        "Character",
        back_populates="scenarios",
        lazy="select",
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_scenarios_category_difficulty", "category", "difficulty"),
        Index("ix_scenarios_active", "is_active", postgresql_where="deleted_at IS NULL"),
        Index("ix_scenarios_tags_gin", "tags", postgresql_using="gin"),
        Index("ix_scenarios_tasks_gin", "tasks", postgresql_using="gin"),
        CheckConstraint("difficulty IN ('easy','medium','hard')", name="ck_scenarios_difficulty"),
    )

    def __repr__(self) -> str:
        return f"<Scenario id={self.id} title={self.title!r}>"
