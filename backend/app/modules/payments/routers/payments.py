from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.payments.schemas.payment import (
    PaymentCheckoutRequest,
    PaymentCheckoutResponse,
    PromoQuoteRequest,
    PromoQuoteResponse,
    PaymentStatusResponse,
    SubscriptionPlanRead,
)
from app.modules.payments.services.payment_service import PaymentService
from app.modules.users.models.user import User

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/plans", response_model=list[SubscriptionPlanRead])
async def list_subscription_plans(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await PaymentService.list_active_subscription_plans(db)


@router.post("/promo/quote", response_model=PromoQuoteResponse)
async def quote_promo_code(
    body: PromoQuoteRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    quote = await PaymentService.quote_checkout(db, plan_code=body.plan_code.strip().upper(), promo_code=body.promo_code)
    promo = quote["promo"]
    return PromoQuoteResponse(
        plan_code=quote["plan"].code,
        promo_code=promo.code,
        original_amount=quote["original_amount"],
        discount_amount=quote["discount_amount"],
        amount=quote["amount"],
        currency=quote["currency"],
        discount_percent=promo.discount_percent,
    )


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
        plan_code=payment.plan_code,
        duration_days=payment.duration_days,
        original_amount=payment.original_amount,
        discount_amount=payment.discount_amount,
        promo_code=payment.promo_code,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        checkout_url=payment.payment_url or "",
        expires_at=payment.expires_at,
    )


@router.get("/transactions/{order_code}", response_model=PaymentStatusResponse)
async def get_payment_status(
    order_code: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payment = await PaymentService.get_payment_for_user(
        db,
        user=user,
        order_code=order_code,
    )
    return PaymentStatusResponse(
        payment_id=payment.id,
        order_code=payment.order_code,
        provider=payment.provider,
        plan=payment.plan,
        plan_code=payment.plan_code,
        duration_days=payment.duration_days,
        original_amount=payment.original_amount,
        discount_amount=payment.discount_amount,
        promo_code=payment.promo_code,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        paid_at=payment.paid_at,
        expires_at=payment.expires_at,
        failure_reason=payment.failure_reason,
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
