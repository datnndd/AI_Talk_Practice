"""Message model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="messages")
    corrections = relationship("Correction", back_populates="message", lazy="selectin")
    score = relationship("MessageScore", back_populates="message", uselist=False, lazy="selectin")
