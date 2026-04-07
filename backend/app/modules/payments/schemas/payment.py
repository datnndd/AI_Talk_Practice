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
