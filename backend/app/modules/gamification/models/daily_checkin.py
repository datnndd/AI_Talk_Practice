from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models.user import User


class DailyCheckin(Base, TimestampMixin):
    __tablename__ = "daily_checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    streak_day: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    coin_earned: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    user: Mapped["User"] = relationship("User", back_populates="daily_checkins")

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_checkins_user_date"),
        Index("ix_daily_checkins_user_date", "user_id", "date"),
    )
