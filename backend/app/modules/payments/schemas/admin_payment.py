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
    paid_revenue_amount: int
    paid_revenue_currency: str = "VND"


class PaymentStatsBucketRead(BaseModel):
    label: str
    period_start: datetime
    paid_revenue_amount: int
    paid_transactions: int
    currency: str = "VND"

class PaymentStatsRead(BaseModel):
    period: str
    currency: str = "VND"
    items: list[PaymentStatsBucketRead]

class AdminPaymentTransactionRead(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_display_name: str | None = None
    provider: str
    plan: str
    plan_code: str | None = None
    duration_days: int | None = None
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


class PaymentStatusBreakdownRead(BaseModel):
    status: str
    transactions: int

class PaymentPlanRevenueRead(BaseModel):
    plan_code: str
    paid_revenue_amount: int
    paid_transactions: int
    currency: str = "VND"

class PaymentDashboardRead(BaseModel):
    period: str
    currency: str = "VND"
    overview: PaymentOverviewRead
    revenue_trend: list[PaymentStatsBucketRead]
    status_breakdown: list[PaymentStatusBreakdownRead]
    plan_revenue_split: list[PaymentPlanRevenueRead]
    recent_payments: list[AdminPaymentTransactionRead]

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
