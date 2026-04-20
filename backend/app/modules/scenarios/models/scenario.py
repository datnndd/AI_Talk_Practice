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
    from app.modules.sessions.models.session import Session
    from app.modules.users.models.user import User


class Scenario(Base, TimestampMixin):
    """
    A conversation scenario template.

    Design notes:
    - `ai_system_prompt` is the scenario-specific instruction used at runtime.
    - `target_skills` JSONB: ["pronunciation", "fluency", "grammar", "vocabulary"]
    - `tags` JSONB: ["airport", "formal", "beginner-friendly"] — aids recommendation.
    - `metadata` JSONB: open extension bag (partner persona, vocab list, etc.).
    - `estimated_duration` in seconds — used for session time predictions in the UI.
    - Soft-delete via `deleted_at` — never hard-delete published scenarios.
    """

    __tablename__ = "scenarios"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── Content ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # JSONB: ["order food politely", "ask about specials"]
    learning_objectives: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="[]")

    ai_system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    ai_role: Mapped[str] = mapped_column(String(500), nullable=False, server_default="")
    user_role: Mapped[str] = mapped_column(String(500), nullable=False, server_default="")

    # ── Classification ────────────────────────────────────────────────────────
    category: Mapped[str] = mapped_column(String(50), nullable=False)     # "travel", "business"
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")
    # JSONB: ["pronunciation", "fluency"]
    target_skills: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="[]")
    # JSONB: ["restaurant", "polite", "formal"]
    tags: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="[]")

    # ── Session parameters ────────────────────────────────────────────────────
    estimated_duration: Mapped[Optional[int]] = mapped_column(SmallInteger)  # seconds
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer)  # New: session time limit in minutes
    # "conversation" | "roleplay" | "debate" | "interview"
    mode: Mapped[str] = mapped_column(String(30), nullable=False, server_default="conversation")

    # ── Extension bag ─────────────────────────────────────────────────────────
    # {"partner_persona": "Friendly barista", "vocab_focus": ["latte", "espresso"]}
    scenario_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSONB, server_default="{}")

    # ── Admin ─────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by], lazy="select")
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="scenario",
        lazy="select",
        passive_deletes=True,
    )
    prompt_history: Mapped[list["ScenarioPromptHistory"]] = relationship(
        "ScenarioPromptHistory",
        back_populates="scenario",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ScenarioPromptHistory.created_at.desc()",
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_scenarios_category_difficulty", "category", "difficulty"),
        Index("ix_scenarios_active", "is_active", postgresql_where="deleted_at IS NULL"),
        Index("ix_scenarios_tags_gin", "tags", postgresql_using="gin"),
        Index("ix_scenarios_target_skills_gin", "target_skills", postgresql_using="gin"),
        CheckConstraint("difficulty IN ('easy','medium','hard')", name="ck_scenarios_difficulty"),
        CheckConstraint(
            "mode IN ('conversation','roleplay','debate','interview','presentation')",
            name="ck_scenarios_mode",
        ),
    )

    def __repr__(self) -> str:
        return f"<Scenario id={self.id} title={self.title!r}>"


class ScenarioPromptHistory(Base, TimestampMixin):
    """Tracks prompt revisions for admin auditing and rollback support."""

    __tablename__ = "scenario_prompt_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    previous_prompt: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    new_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    change_note: Mapped[Optional[str]] = mapped_column(String(255))
    quality_score: Mapped[Optional[int]] = mapped_column(Integer)
    changed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="prompt_history", lazy="select")
    changer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[changed_by], lazy="select")

    __table_args__ = (
        Index("ix_scenario_prompt_history_scenario", "scenario_id", "created_at"),
    )
