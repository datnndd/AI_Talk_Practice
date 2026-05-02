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
    plan_code: str | None = None
    duration_days: int | None = None
    original_amount: int | None = None
    discount_amount: int = 0
    promo_code: str | None = None
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


class AdminSubscriptionPlanRead(BaseModel):
    id: int
    code: str
    name: str
    duration_days: int
    price_amount: int
    currency: str
    is_active: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class AdminSubscriptionPlanUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_amount: int = Field(ge=0)
    is_active: bool = True
    sort_order: int = 0


class AdminPromotionCodeRead(BaseModel):
    id: int
    code: str
    discount_percent: int
    is_active: bool
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_redemptions: int | None = None
    redeemed_count: int

    model_config = ConfigDict(from_attributes=True)


class AdminPromotionCodeCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    discount_percent: int = Field(ge=1, le=100)
    is_active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_redemptions: int | None = Field(default=None, ge=1)


class AdminPromotionCodeUpdateRequest(BaseModel):
    discount_percent: int = Field(ge=1, le=100)
    is_active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_redemptions: int | None = Field(default=None, ge=1)
