from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class PhonemeError(Base, TimestampMixin):
    __tablename__ = "phoneme_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    phoneme: Mapped[str] = mapped_column(String(20))          # "/θ/", "/r/"...
    error_count: Mapped[int] = mapped_column(Integer, server_default="1")
    avg_severity: Mapped[float] = mapped_column(Float)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User")  # type: ignore

    __table_args__ = (UniqueConstraint("user_id", "phoneme"),)