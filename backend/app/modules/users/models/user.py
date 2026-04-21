from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.sessions.models.session import Session
    from app.modules.gamification.models.daily_stat import DailyStat
    from app.modules.gamification.models.gem_transaction import GemTransaction
    from app.modules.gamification.models.user_achievement import UserAchievement
    from app.modules.users.models.subscription import Subscription
    # If these exist elsewhere, point to them
    # from app.models.recording import Recording
    # from app.models.subscription import Subscription


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Auth
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(20), server_default="local")
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

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
    current_streak: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_completed_lesson_date: Mapped[Optional[date]] = mapped_column(Date)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    daily_xp_goal: Mapped[int] = mapped_column(Integer, default=50, server_default="50")
    gem_balance: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    heart_balance: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    heart_max: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    last_heart_refill_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    total_lessons_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_speaking_lessons_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_vocabulary_lessons_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    perfect_score_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    daily_goal_streak: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_daily_goal_date: Mapped[Optional[date]] = mapped_column(Date)
    total_practice_minutes: Mapped[int] = mapped_column(Integer, server_default="0")

    # Onboarding JSONB
    favorite_topics: Mapped[Optional[Any]] = mapped_column(JSONB)
    learning_purpose: Mapped[Optional[Any]] = mapped_column(JSONB)
    main_challenge: Mapped[Optional[str]] = mapped_column(String(500))
    daily_goal: Mapped[Optional[int]] = mapped_column(SmallInteger)
    is_onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    # Extension
    preferences: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="{}")

    # Soft-delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user", lazy="select", cascade="all, delete-orphan")
    daily_stats: Mapped[list["DailyStat"]] = relationship("DailyStat", back_populates="user")
    achievements: Mapped[list["UserAchievement"]] = relationship("UserAchievement", back_populates="user")
    gem_transactions: Mapped[list["GemTransaction"]] = relationship("GemTransaction", back_populates="user")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="user", uselist=False, lazy="selectin")

    __table_args__ = (
        # Basic index for email, avoids postgresql_where for SQLite compatibility
        Index("ix_users_email_active", "email"),
        # Gin index is PG only, SQLAlchemy usually ignores it on other dialects 
        # but we keep it simple here.
        Index("ix_users_favorite_topics_idx", "favorite_topics"),
    )
