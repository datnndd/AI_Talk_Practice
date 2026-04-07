from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PaymentOverviewRead(BaseModel):
    total_transactions: int
    pending_transactions: int
    paid_transactions: int
    failed_transactions: int
    cancelled_transactions: int
    paid_revenue_usd_cents: int


class AdminPaymentTransactionRead(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_display_name: str | None = None
    provider: str
    plan: str
    amount: int
    currency: str
    status: str
    order_code: str
    external_checkout_id: str | None = None
    external_transaction_id: str | None = None
    payment_url: str | None = None
    failure_reason: str | None = None
    provider_payload: dict[str, Any] | None = None
    paid_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminPaymentListResponse(BaseModel):
    items: list[AdminPaymentTransactionRead]
    total: int
    page: int
    page_size: int


class AdminPaymentStatusUpdateRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)
