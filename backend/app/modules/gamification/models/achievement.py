from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

class Achievement(Base):
    __tablename__ = "achievements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    icon_url: Mapped[Optional[str]] = mapped_column(String(500))
    gem_reward: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    condition: Mapped[Any] = mapped_column(JSONB)   # {"streak": 7, "score": 90}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
