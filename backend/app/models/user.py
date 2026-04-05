from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.recording import Recording
    from app.models.daily_stat import DailyStat
    from app.models.user_achievement import UserAchievement
    from app.models.subscription import Subscription


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Auth
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar: Mapped[Optional[str]] = mapped_column(String(500))
    age: Mapped[Optional[int]] = mapped_column(SmallInteger)

    # Language & Level
    native_language: Mapped[Optional[str]] = mapped_column(String(10))
    target_language: Mapped[Optional[str]] = mapped_column(String(10))
    target_accent: Mapped[Optional[str]] = mapped_column(String(20))
    level: Mapped[Optional[str]] = mapped_column(String(20))
    current_cefr: Mapped[Optional[str]] = mapped_column(String(10))

    # Streak & Progress
    current_streak: Mapped[int] = mapped_column(Integer, server_default="0")
    longest_streak: Mapped[int] = mapped_column(Integer, server_default="0")
    total_practice_minutes: Mapped[int] = mapped_column(Integer, server_default="0")

    # Onboarding JSONB
    favorite_topics: Mapped[Optional[Any]] = mapped_column(JSONB)
    learning_purpose: Mapped[Optional[Any]] = mapped_column(JSONB)
    main_challenge: Mapped[Optional[str]] = mapped_column(String(500))
    daily_goal: Mapped[Optional[int]] = mapped_column(SmallInteger)
    is_onboarding_completed: Mapped[bool] = mapped_column(Boolean, server_default="false")

    # Extension
    preferences: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="{}")

    # Soft-delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user", lazy="select", cascade="all, delete-orphan")
    daily_stats: Mapped[list["DailyStat"]] = relationship("DailyStat", back_populates="user")
    achievements: Mapped[list["UserAchievement"]] = relationship("UserAchievement", back_populates="user")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="user", uselist=False)

    __table_args__ = (
        Index("ix_users_email_active", "email", postgresql_where="deleted_at IS NULL"),
        Index("ix_users_favorite_topics_gin", "favorite_topics", postgresql_using="gin"),
    )