"""Session model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    scenario_id: Mapped[int] = mapped_column(Integer, ForeignKey("scenarios.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    scenario = relationship("Scenario", back_populates="sessions")
    messages = relationship("Message", back_populates="session", lazy="selectin", order_by="Message.order_index")
    score = relationship("SessionScore", back_populates="session", uselist=False, lazy="selectin")
