"""Scenario model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    learning_objectives: Mapped[str] = mapped_column(Text, default="")
    ai_system_prompt: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), index=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    sessions = relationship("Session", back_populates="scenario", lazy="selectin")
