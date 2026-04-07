from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin


class PaymentWebhookEvent(Base, TimestampMixin):
    __tablename__ = "payment_webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(20), index=True)
    event_id: Mapped[str] = mapped_column(String(255), index=True)
    event_type: Mapped[Optional[str]] = mapped_column(String(100))
    payload: Mapped[Optional[Any]] = mapped_column(JSONB)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_payment_webhook_events_provider_event_id"),
    )
