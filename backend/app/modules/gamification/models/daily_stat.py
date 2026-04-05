from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.modules.users.models.user import User


class DailyStat(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    minutes_practiced: Mapped[int] = mapped_column(Integer, server_default="0")
    avg_score: Mapped[Optional[float]] = mapped_column(Float)
    recordings_count: Mapped[int] = mapped_column(Integer, server_default="0")

    user: Mapped["User"] = relationship("User", back_populates="daily_stats")

    __table_args__ = (UniqueConstraint("user_id", "date"),)