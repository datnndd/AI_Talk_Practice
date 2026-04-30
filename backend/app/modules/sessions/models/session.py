"""Session model — production-grade practice-session tracking with soft-delete."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.characters.models.character import Character
    from app.modules.sessions.models.message import Message
    from app.modules.scenarios.models.scenario import Scenario
    from app.modules.sessions.models.session_score import SessionScore
    from app.modules.users.models.user import User


class Session(Base, TimestampMixin):
    """
    A single practice session between a user and the AI partner.

    Design notes:
    - `session_metadata` JSONB captures runtime context that doesn't need its own
      column: {"asr_engine": "dashscope", "tts_voice": "...", ...}
    - `deleted_at` soft-delete: sessions are never hard-deleted for audit trail.
    - `messages` lazy="select" — ALWAYS load via selectinload() in queries, not
      implicitly, to prevent N+1 across session lists.
    """

    __tablename__ = "sessions"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── FKs ───────────────────────────────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    scenario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scenarios.id", ondelete="RESTRICT"), nullable=False
    )
    character_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("characters.id", ondelete="SET NULL"), nullable=True
    )
    # ── Status ────────────────────────────────────────────────────────────────
    # "active" | "completed" | "abandoned" | "error"
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")

    # ── Timing ───────────────────────────────────────────────────────────────
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    # ── Runtime metadata ─────────────────────────────────────────────────────
    # {"asr_engine": "dashscope", "tts_voice": "...", "llm_model": "ai-talk"}
    session_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSONB, server_default="{}")

    # ── Soft-delete ───────────────────────────────────────────────────────────
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="sessions", lazy="select")
    scenario: Mapped["Scenario"] = relationship("Scenario", back_populates="sessions", lazy="select")
    character: Mapped[Optional["Character"]] = relationship("Character", back_populates="sessions", lazy="select")
    # lazy="select" — load explicitly with selectinload() to avoid N+1
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        lazy="select",
        order_by="Message.order_index",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    score: Mapped[Optional["SessionScore"]] = relationship(
        "SessionScore",
        back_populates="session",
        uselist=False,
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        # Most common query pattern: "all active sessions for a user, recent first"
        Index("ix_sessions_user_status_started", "user_id", "status", "started_at"),
        # Dashboard: sessions per scenario
        Index("ix_sessions_scenario_status", "scenario_id", "status"),
        Index("ix_sessions_character_id", "character_id"),
        Index("ix_sessions_started_at", "started_at"),
        # Partial: live sessions (dashboard monitoring)
        Index(
            "ix_sessions_active_live",
            "user_id",
            "started_at",
            postgresql_where="status = 'active' AND deleted_at IS NULL",
        ),
        CheckConstraint(
            "status IN ('active','completed','abandoned','error')",
            name="ck_sessions_status",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_sessions_timing",
        ),
    )

    def __repr__(self) -> str:
        return f"<Session id={self.id} user_id={self.user_id} status={self.status!r}>"
