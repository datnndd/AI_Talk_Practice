from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCheckoutRequest(BaseModel):
    provider: Literal["stripe"]
    plan: Literal["PRO"] = "PRO"


class PaymentCheckoutResponse(BaseModel):
    payment_id: int
    order_code: str
    provider: str
    plan: str
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
    amount: int
    currency: str
    status: str
    paid_at: datetime | None = None
    expires_at: datetime | None = None
    failure_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)
