"""User model — production-grade with JSONB preferences and soft-delete."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.session import Session


class User(Base, TimestampMixin):
    """
    Application user.

    Design notes:
    - Multi-valued onboarding fields (favorite_topics, learning_purpose) stored
      as JSONB so they can hold lists/dicts without VARCHAR length limits and
      can be queried/indexed efficiently.
    - `preferences` JSONB acts as a forward-compatible extension bag (notifications,
      UI settings, etc.) without schema migrations.
    - Soft-delete via `deleted_at`: rows are never hard-deleted so analytics and
      FK integrity are preserved.
    - `sessions` uses lazy="dynamic" (select-on-demand) at the User level because
      a user can accumulate thousands of sessions; callers should paginate.
    """

    __tablename__ = "users"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── Auth ─────────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Profile ───────────────────────────────────────────────────────────────
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar: Mapped[Optional[str]] = mapped_column(String(500))
    age: Mapped[Optional[int]] = mapped_column(SmallInteger)

    # ── Language settings ─────────────────────────────────────────────────────
    native_language: Mapped[Optional[str]] = mapped_column(String(10))   # BCP-47, e.g. "vi"
    target_language: Mapped[Optional[str]] = mapped_column(String(10))   # BCP-47, e.g. "en"
    level: Mapped[Optional[str]] = mapped_column(String(20))             # A1–C2

    # ── Onboarding — JSONB instead of VARCHAR(500) lists ─────────────────────
    # favorite_topics: ["travel", "business", "tech"]
    favorite_topics: Mapped[Optional[Any]] = mapped_column(JSONB)
    # learning_purpose: "career" | or list ["career", "travel"]
    learning_purpose: Mapped[Optional[Any]] = mapped_column(JSONB)
    main_challenge: Mapped[Optional[str]] = mapped_column(String(500))
    daily_goal: Mapped[Optional[int]] = mapped_column(SmallInteger)       # minutes/day
    is_onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Extension bag ─────────────────────────────────────────────────────────
    # {"notifications": true, "ui_theme": "dark", "reminder_time": "08:00"}
    preferences: Mapped[Optional[Any]] = mapped_column(JSONB, server_default="{}")

    # ── Soft-delete ───────────────────────────────────────────────────────────
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    # lazy="select" (default) — do NOT eagerly load all sessions when querying a user
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        # Partial index: only active (non-deleted) users
        Index("ix_users_email_active", "email", postgresql_where="deleted_at IS NULL"),
        # GIN index for JSONB topic queries
        Index("ix_users_favorite_topics_gin", "favorite_topics", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
