"""MessageScore model — per-utterance pronunciation + language evaluation."""

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
    from app.modules.sessions.models.message import Message


class MessageScore(Base, TimestampMixin):
    """
    Per-message (utterance) evaluation scores from ASR + LLM grading.

    Design notes:
    - All sub-scores are 0.0–10.0 (not 1–10) for mathematical convenience
      (avg, percentile). CHECK constraints enforce the range.
    - `mispronounced_words` replaces generic JSON with PostgreSQL JSONB for
      efficient querying ("find all sessions with >3 mispronounced words").
      Schema: [{"word": "restaurant", "user_ipa": "/res.tau.rant/",
                "correct_ipa": "/ˈrɛs.tər.ənt/", "severity": "high"}]
    - `score_metadata` holds raw LLM grader output and confidence for audit.
    - UniqueConstraint(message_id) enforces one score per message at the DB level
      (not just Python).
    - Only scored for role="user" messages; assistant messages will not have a score.
    """

    __tablename__ = "message_scores"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── FK ────────────────────────────────────────────────────────────────────
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )

    # ── Scores (0.0–10.0) ─────────────────────────────────────────────────────
    pronunciation_score: Mapped[float] = mapped_column(Float, nullable=False)
    fluency_score: Mapped[float] = mapped_column(Float, nullable=False)
    grammar_score: Mapped[float] = mapped_column(Float, nullable=False)
    vocabulary_score: Mapped[float] = mapped_column(Float, nullable=False)
    intonation_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)  # weighted avg

    # ── Detailed feedback ─────────────────────────────────────────────────────
    # JSONB: [{"word": "...", "user_ipa": "...", "correct_ipa": "...", "severity": "high"}]
    mispronounced_words: Mapped[Optional[Any]] = mapped_column(JSONB)
    feedback: Mapped[Optional[str]] = mapped_column(Text)

    # ── Grader provenance ─────────────────────────────────────────────────────
    # {"model": "ai-talk", "latency_ms": 320, "raw_response": {...}}
    score_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSONB)

    # ── Relationships ─────────────────────────────────────────────────────────
    message: Mapped["Message"] = relationship("Message", back_populates="score")

    # ── Indexes & constraints ─────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("message_id", name="uq_message_scores_message_id"),
        Index("ix_message_scores_message_id", "message_id"),
        # Analytics: find low-scoring messages across sessions
        Index("ix_message_scores_overall", "overall_score"),
        # Range checks — all scores 0–10
        CheckConstraint("pronunciation_score BETWEEN 0 AND 10", name="ck_ms_pronunciation"),
        CheckConstraint("fluency_score BETWEEN 0 AND 10", name="ck_ms_fluency"),
        CheckConstraint("grammar_score BETWEEN 0 AND 10", name="ck_ms_grammar"),
        CheckConstraint("vocabulary_score BETWEEN 0 AND 10", name="ck_ms_vocabulary"),
        CheckConstraint("intonation_score BETWEEN 0 AND 10", name="ck_ms_intonation"),
        CheckConstraint("overall_score BETWEEN 0 AND 10", name="ck_ms_overall"),
    )

    def __repr__(self) -> str:
        return (
            f"<MessageScore id={self.id} message_id={self.message_id} "
            f"overall={self.overall_score:.1f}>"
        )
