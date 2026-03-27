"""User model."""

from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100), nullable=True)
    native_language: Mapped[str] = mapped_column(String(10), nullable=True)
    target_language: Mapped[str] = mapped_column(String(10), nullable=True)
    level: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Onboarding fields
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    age: Mapped[int] = mapped_column(nullable=True)
    learning_purpose: Mapped[str] = mapped_column(String(500), nullable=True)
    main_challenge: Mapped[str] = mapped_column(String(500), nullable=True)
    favorite_topics: Mapped[str] = mapped_column(String(500), nullable=True)
    daily_goal: Mapped[int] = mapped_column(nullable=True)
    is_onboarding_completed: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    sessions = relationship("Session", back_populates="user", lazy="selectin")
