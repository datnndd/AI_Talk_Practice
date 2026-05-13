"""Realtime feedback model for simplified message correction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Index, Integer, JSON, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


if TYPE_CHECKING:
    from app.modules.sessions.models.message import Message


class MessageRealtimeFeedback(Base, TimestampMixin):
    """Latest realtime speaking feedback attached to one user message."""

    __tablename__ = "message_realtime_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_good: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    better_answer: Mapped[str | None] = mapped_column(Text)
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    message: Mapped["Message"] = relationship("Message", back_populates="realtime_feedback")

    __table_args__ = (
        UniqueConstraint("message_id", name="uq_message_realtime_feedbacks_message_id"),
        Index("ix_message_realtime_feedbacks_message_id", "message_id"),
    )

    def __repr__(self) -> str:
        return f"<MessageRealtimeFeedback id={self.id} message_id={self.message_id}>"
