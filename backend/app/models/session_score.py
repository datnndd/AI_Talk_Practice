"""SessionScore model — aggregated scores from all message_scores."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class SessionScore(Base, TimestampMixin):
    __tablename__ = "session_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), unique=True, index=True)
    avg_pronunciation: Mapped[float] = mapped_column(Float)
    avg_fluency: Mapped[float] = mapped_column(Float)
    avg_grammar: Mapped[float] = mapped_column(Float)
    avg_vocabulary: Mapped[float] = mapped_column(Float)
    avg_intonation: Mapped[float] = mapped_column(Float)
    relevance_score: Mapped[float] = mapped_column(Float)   # evaluated separately at session end
    overall_score: Mapped[float] = mapped_column(Float)
    feedback_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # (scored_at replaced by created_at via TimestampMixin)

    # Relationships
    session = relationship("Session", back_populates="score")
