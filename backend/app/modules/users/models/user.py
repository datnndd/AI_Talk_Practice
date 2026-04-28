from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.sessions.models.session import Session
    from app.modules.gamification.models.daily_checkin import DailyCheckin
    from app.modules.gamification.models.daily_stat import DailyStat
    from app.modules.gamification.models.coin_transaction import CoinTransaction
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
    role: Mapped[str] = mapped_column(String(20), default="user", server_default="user")
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    # Profile
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar: Mapped[Optional[str]] = mapped_column(String(500))
    age: Mapped[Optional[int]] = mapped_column(SmallInteger)

    # Level
    level: Mapped[Optional[str]] = mapped_column(String(20))
    current_cefr: Mapped[Optional[str]] = mapped_column(String(10))

    # Gamification progress
    total_xp: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    coin_balance: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_lessons_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_speaking_lessons_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_vocabulary_lessons_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    perfect_score_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
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
    daily_checkins: Mapped[list["DailyCheckin"]] = relationship("DailyCheckin", back_populates="user")
    daily_stats: Mapped[list["DailyStat"]] = relationship("DailyStat", back_populates="user")
    coin_transactions: Mapped[list["CoinTransaction"]] = relationship("CoinTransaction", back_populates="user")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="user", uselist=False, lazy="selectin")

    __table_args__ = (
        # Basic index for email, avoids postgresql_where for SQLite compatibility
        Index("ix_users_email_active", "email"),
        # Gin index is PG only, SQLAlchemy usually ignores it on other dialects 
        # but we keep it simple here.
        Index("ix_users_favorite_topics_idx", "favorite_topics"),
    )
