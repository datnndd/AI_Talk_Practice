from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCheckoutRequest(BaseModel):
    provider: Literal["stripe"]
    plan: Literal["PRO"] = "PRO"
    plan_code: str | None = Field(default=None, max_length=40)
    promo_code: str | None = Field(default=None, max_length=40)


class SubscriptionPlanRead(BaseModel):
    code: str
    name: str
    duration_days: int
    price_amount: int
    currency: str
    is_active: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class PromoQuoteRequest(BaseModel):
    plan_code: str = Field(max_length=40)
    promo_code: str = Field(max_length=40)


class PromoQuoteResponse(BaseModel):
    plan_code: str
    promo_code: str
    original_amount: int
    discount_amount: int
    amount: int
    currency: str
    discount_percent: int


class PaymentCheckoutResponse(BaseModel):
    payment_id: int
    order_code: str
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
    checkout_url: str
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PaymentStatusResponse(BaseModel):
    payment_id: int
    order_code: str
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
    paid_at: datetime | None = None
    expires_at: datetime | None = None
    failure_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)
