"""MessageScore model — per-utterance pronunciation evaluation."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Float, Text, Integer, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MessageScore(Base):
    __tablename__ = "message_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id"), unique=True, index=True)
    pronunciation_score: Mapped[float] = mapped_column(Float)   # 1–10
    fluency_score: Mapped[float] = mapped_column(Float)          # 1–10
    grammar_score: Mapped[float] = mapped_column(Float)          # 1–10
    vocabulary_score: Mapped[float] = mapped_column(Float)       # 1–10
    intonation_score: Mapped[float] = mapped_column(Float)       # 1–10
    overall_score: Mapped[float] = mapped_column(Float)          # average of 5
    mispronounced_words: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    # Example: [{"word": "restaurant", "user_said": "/res-tau-rant/", "correct_ipa": "/ˈrɛstərɒnt/"}]
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("Message", back_populates="score")
