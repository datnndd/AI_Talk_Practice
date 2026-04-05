"""Correction model — grammar/vocabulary/naturalness corrections on user utterances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.sessions.models.message import Message


class Correction(Base, TimestampMixin):
    """
    A specific language correction attached to a user Message.

    Design notes:
    - One Message can have multiple Correction rows (grammar + vocabulary, etc.).
    - `error_type` is constrained to a known enum-like set to prevent data drift.
    - `severity` (low/medium/high) allows UI to prioritise which corrections to
      surface first, and lets analytics filter by impact.
    - `position_start` / `position_end` are character offsets into `message.content`
      so the frontend can highlight the exact error span without string parsing.
    """

    __tablename__ = "corrections"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── FK ────────────────────────────────────────────────────────────────────
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )

    # ── Content ───────────────────────────────────────────────────────────────
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Classification ────────────────────────────────────────────────────────
    # "grammar" | "vocabulary" | "naturalness" | "pronunciation" | "register"
    error_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # "low" | "medium" | "high"
    severity: Mapped[str] = mapped_column(String(10), nullable=False, server_default="medium")

    # ── Position in original text (character offsets, nullable) ───────────────
    position_start: Mapped[int | None] = mapped_column(SmallInteger)
    position_end: Mapped[int | None] = mapped_column(SmallInteger)

    # ── Relationships ─────────────────────────────────────────────────────────
    message: Mapped["Message"] = relationship("Message", back_populates="corrections")

    # ── Indexes & constraints ─────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_corrections_message_id", "message_id"),
        Index("ix_corrections_error_type", "error_type"),
        CheckConstraint(
            "error_type IN ('grammar','vocabulary','naturalness','pronunciation','register')",
            name="ck_corrections_error_type",
        ),
        CheckConstraint(
            "severity IN ('low','medium','high')",
            name="ck_corrections_severity",
        ),
        CheckConstraint(
            "(position_start IS NULL AND position_end IS NULL) OR "
            "(position_start IS NOT NULL AND position_end IS NOT NULL AND position_end >= position_start)",
            name="ck_corrections_position",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Correction id={self.id} message_id={self.message_id} "
            f"type={self.error_type!r} severity={self.severity!r}>"
        )
