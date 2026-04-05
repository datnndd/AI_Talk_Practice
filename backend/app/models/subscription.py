from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    tier: Mapped[str] = mapped_column(String(20))          # FREE / PRO / ENTERPRISE
    status: Mapped[str] = mapped_column(String(20))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    features: Mapped[Optional[Any]] = mapped_column(JSONB)

    user: Mapped["User"] = relationship("User", back_populates="subscription")