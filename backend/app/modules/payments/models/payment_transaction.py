from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models.user import User


class PaymentTransaction(Base, TimestampMixin):
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(20), index=True)
    plan: Mapped[str] = mapped_column(String(20))
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), index=True)
    order_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    external_checkout_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    external_transaction_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    payment_url: Mapped[Optional[str]] = mapped_column(Text)
    provider_payload: Mapped[Optional[Any]] = mapped_column(JSONB)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_payment_transactions_provider_status", "provider", "status"),
    )
