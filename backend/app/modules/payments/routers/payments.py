from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.payments.schemas.payment import PaymentCheckoutRequest, PaymentCheckoutResponse
from app.modules.payments.services.payment_service import PaymentService
from app.modules.users.models.user import User

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/checkout", response_model=PaymentCheckoutResponse)
async def create_checkout(
    body: PaymentCheckoutRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payment = await PaymentService.create_checkout(
        db,
        user=user,
        body=body,
        client_ip=request.headers.get("x-forwarded-for") or (request.client.host if request.client else None),
    )
    return PaymentCheckoutResponse(
        payment_id=payment.id,
        order_code=payment.order_code,
        provider=payment.provider,
        plan=payment.plan,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        checkout_url=payment.payment_url or "",
        expires_at=payment.expires_at,
    )


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    return await PaymentService.process_stripe_webhook(
        db,
        payload=payload,
        signature=signature,
    )

