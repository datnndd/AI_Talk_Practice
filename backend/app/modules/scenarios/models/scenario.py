"""Scenario + ScenarioVariation models — hybrid pre-generate + real-time LLM system."""

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
    UniqueConstraint,
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
    - `ai_system_prompt` is the *base* system prompt; variations override/extend it.
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
    opening_message: Mapped[Optional[str]] = mapped_column(Text)

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
    starter: Mapped[str] = mapped_column(String(10), server_default="AI")  # 'AI' or 'USER' - who starts
    # "conversation" | "roleplay" | "debate" | "interview"
    mode: Mapped[str] = mapped_column(String(30), nullable=False, server_default="conversation")
    is_ai_start_first: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # ── Extension bag ─────────────────────────────────────────────────────────
    # {"partner_persona": "Friendly barista", "vocab_focus": ["latte", "espresso"]}
    scenario_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSONB, server_default="{}")

    # ── Admin ─────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_pre_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    pre_gen_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="8")
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by], lazy="select")
    variations: Mapped[list["ScenarioVariation"]] = relationship(
        "ScenarioVariation",
        back_populates="scenario",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
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
        CheckConstraint("pre_gen_count >= 0", name="ck_scenarios_pre_gen_count_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<Scenario id={self.id} title={self.title!r}>"


class ScenarioVariation(Base, TimestampMixin):
    """
    Pre-generated (or cached real-time) variation of a Scenario.

    Hybrid strategy:
    - Pre-generated variations: created offline/batch, stored here with
      `is_pregenerated=True` and a unique `variation_seed`.
    - Real-time LLM variations: generated on-demand, cached here after first use
      so subsequent sessions with same parameters skip LLM.

    The `parameters` JSONB captures what was varied:
        {"proficiency": "B1", "formality": "casual", "topic_twist": "it's your first day"}

    `sample_prompt` is an optional human-readable teaser shown in the UI.
    `usage_count` is incremented each time a session uses this variation (for analytics
    + load balancing: favour less-used variants for fairness).
    """

    __tablename__ = "scenario_variations"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── FK ────────────────────────────────────────────────────────────────────
    scenario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )

    # ── Variation identity ────────────────────────────────────────────────────
    # Deterministic seed: sha256(scenario_id || sorted(parameters))[:16]
    # Used to deduplicate: same seed → same variation → reuse existing row.
    variation_seed: Mapped[str] = mapped_column(String(64), nullable=False)

    # ── Generated content ─────────────────────────────────────────────────────
    variation_name: Mapped[str] = mapped_column(String(160), nullable=False, server_default="Untitled variation")
    # JSONB: {"proficiency": "B1", "formality": "casual", "topic_twist": "..."}
    parameters: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default="{}")
    # Full system prompt override for this variation (if None, use Scenario.ai_system_prompt)
    system_prompt_override: Mapped[Optional[str]] = mapped_column(Text)
    # Short teaser shown in the UI: "You're a nervous first-timer at customs"
    sample_prompt: Mapped[Optional[str]] = mapped_column(String(500))
    # JSON conversation preview used by admins before approving the variation.
    sample_conversation: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="[]")

    # ── Provenance ────────────────────────────────────────────────────────────
    is_pregenerated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # Which LLM model generated this variation, e.g. "ai-talk"
    generated_by_model: Mapped[Optional[str]] = mapped_column(String(100))
    # LLM generation latency in ms — useful for cost/latency analytics
    generation_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)

    # ── Usage analytics ───────────────────────────────────────────────────────
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Quality flag ─────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # ── Relationships ─────────────────────────────────────────────────────────
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="variations")
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="variation",
        lazy="select",
        passive_deletes=True,
    )

    # ── Indexes & constraints ─────────────────────────────────────────────────
    __table_args__ = (
        # Unique: one variation per seed per scenario
        UniqueConstraint("scenario_id", "variation_seed", name="uq_scenario_variation_seed"),
        Index("ix_scenario_variations_scenario_id", "scenario_id"),
        Index("ix_scenario_variations_pregenerated", "scenario_id", "is_pregenerated", "is_approved"),
        Index("ix_scenario_variations_active", "scenario_id", "is_active"),
        Index("ix_scenario_variations_parameters_gin", "parameters", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return (
            f"<ScenarioVariation id={self.id} scenario_id={self.scenario_id} "
            f"seed={self.variation_seed!r}>"
        )


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
