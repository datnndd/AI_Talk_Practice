"""Character model for Live2D avatar and TTS voice configuration."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.scenarios.models.scenario import Scenario
    from app.modules.sessions.models.session import Session


class Character(Base, TimestampMixin):
    """A reusable AI partner persona with Live2D assets and TTS settings."""

    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    model_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    core_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000))
    tts_voice: Mapped[str] = mapped_column(String(100), nullable=False, server_default="Cherry")
    tts_language: Mapped[str] = mapped_column(String(20), nullable=False, server_default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    character_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSONB, server_default="{}")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    scenarios: Mapped[list["Scenario"]] = relationship(
        "Scenario",
        back_populates="character",
        lazy="select",
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="character",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_characters_active", "is_active", postgresql_where="deleted_at IS NULL"),
        Index("ix_characters_sort_order", "sort_order", "id"),
    )

    def __repr__(self) -> str:
        return f"<Character id={self.id} name={self.name!r}>"
