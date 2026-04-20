"""SessionScore model — aggregated scores computed at session end."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.sessions.models.session import Session


class SessionScore(Base, TimestampMixin):
    """
    Aggregated score for an entire session, computed when session ends.

    Design notes:
    - Scores are produced by post-session evaluation.
    - `scored_message_count` tracks how many messages contributed — needed to
      detect sessions with too few messages to be meaningful.
    - `skill_breakdown` JSONB allows storing per-skill details/trends without
      extra columns:
        {"pronunciation": {"avg": 7.2, "trend": "improving"},
         "fluency": {"avg": 6.8, "trend": "stable"}}
    - `relevance_score` is evaluated separately by LLM at session end
      (0.0–10.0: did the user stay on topic?).
    - `feedback_summary` is LLM-generated natural language summary.
    - Aggregation query hint: use PostgreSQL window functions or a single
      SELECT AVG(...) GROUP BY session_id rather than ORM iteration.
    """

    __tablename__ = "session_scores"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── FK ────────────────────────────────────────────────────────────────────
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )

    # ── Aggregated scores (0.0–10.0) ─────────────────────────────────────────
    avg_pronunciation: Mapped[float] = mapped_column(Float, nullable=False)
    avg_fluency: Mapped[float] = mapped_column(Float, nullable=False)
    avg_grammar: Mapped[float] = mapped_column(Float, nullable=False)
    avg_vocabulary: Mapped[float] = mapped_column(Float, nullable=False)
    avg_intonation: Mapped[float] = mapped_column(Float, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Aggregation metadata ──────────────────────────────────────────────────
    scored_message_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # ── Per-skill details ─────────────────────────────────────────────────────
    # {"pronunciation": {"avg": 7.2}, "grammar": {"avg": 8.1}}
    skill_breakdown: Mapped[Optional[Any]] = mapped_column(JSONB)

    # ── Narrative feedback ────────────────────────────────────────────────────
    feedback_summary: Mapped[Optional[str]] = mapped_column(Text)

    # ── Grader provenance ─────────────────────────────────────────────────────
    # {"model": "ai-talk", "latency_ms": 850}
    score_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSONB)

    # ── Relationships ─────────────────────────────────────────────────────────
    session: Mapped["Session"] = relationship("Session", back_populates="score")

    # ── Indexes & constraints ─────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_session_scores_session_id"),
        Index("ix_session_scores_session_id", "session_id"),
        # Leaderboard / analytics queries
        Index("ix_session_scores_overall", "overall_score"),
        # Range checks
        CheckConstraint("avg_pronunciation BETWEEN 0 AND 10", name="ck_ss_pronunciation"),
        CheckConstraint("avg_fluency BETWEEN 0 AND 10", name="ck_ss_fluency"),
        CheckConstraint("avg_grammar BETWEEN 0 AND 10", name="ck_ss_grammar"),
        CheckConstraint("avg_vocabulary BETWEEN 0 AND 10", name="ck_ss_vocabulary"),
        CheckConstraint("avg_intonation BETWEEN 0 AND 10", name="ck_ss_intonation"),
        CheckConstraint("relevance_score BETWEEN 0 AND 10", name="ck_ss_relevance"),
        CheckConstraint("overall_score BETWEEN 0 AND 10", name="ck_ss_overall"),
        CheckConstraint("scored_message_count >= 0", name="ck_ss_scored_count"),
    )

    def __repr__(self) -> str:
        return (
            f"<SessionScore id={self.id} session_id={self.session_id} "
            f"overall={self.overall_score:.1f}>"
        )
