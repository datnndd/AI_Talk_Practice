"""Message model — per-utterance transcript with optional stored audio."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.sessions.models.message_realtime_feedback import MessageRealtimeFeedback
    from app.modules.sessions.models.session import Session


class Message(Base, TimestampMixin):
    """
    A single spoken turn within a Session.

    Design notes:
    - `role`: "user" (learner) or "assistant" (AI partner).
    - `content`: transcript text (ASR result for user, LLM output for assistant).
    - `audio_url`: path/URL to stored audio file (S3, GCS, etc.).
    - `order_index` + UniqueConstraint(session_id, order_index): enforces message
      ordering and prevents duplicate positions.
    - `realtime_feedback` loaded lazily — always use selectinload() in batch queries
      to prevent N+1.
    """

    __tablename__ = "messages"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── FK ────────────────────────────────────────────────────────────────────
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )

    # ── Content ───────────────────────────────────────────────────────────────
    role: Mapped[str] = mapped_column(String(20), nullable=False)      # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Audio ─────────────────────────────────────────────────────────────────
    audio_url: Mapped[Optional[str]] = mapped_column(String(1000))     # S3/GCS signed URL

    # ── Relationships ─────────────────────────────────────────────────────────
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    realtime_feedback: Mapped[Optional["MessageRealtimeFeedback"]] = relationship(
        "MessageRealtimeFeedback",
        back_populates="message",
        uselist=False,
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # ── Indexes & constraints ─────────────────────────────────────────────────
    __table_args__ = (
        # Core access pattern: fetch all messages for a session, ordered
        Index("ix_messages_session_order", "session_id", "order_index"),
        # Prevent duplicate order indices within a session
        UniqueConstraint("session_id", "order_index", name="uq_messages_session_order"),
        CheckConstraint("role IN ('user', 'assistant')", name="ck_messages_role"),
        CheckConstraint("order_index >= 0", name="ck_messages_order_index_positive"),
    )

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id} session_id={self.session_id} "
            f"role={self.role!r} order={self.order_index}>"
        )
