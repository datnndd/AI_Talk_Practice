from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
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


@router.get("/vnpay/ipn")
async def vnpay_ipn(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    _, success, rsp_code = await PaymentService.process_vnpay_response(
        db,
        query_params=dict(request.query_params),
    )
    return {
        "RspCode": "00" if success else rsp_code,
        "Message": "Confirm Success" if success else "Confirm Failed",
    }


@router.get("/vnpay/return")
async def vnpay_return(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payment, success, rsp_code = await PaymentService.process_vnpay_response(
        db,
        query_params=dict(request.query_params),
    )
    status = "success" if success else "failed"
    redirect_url = PaymentService._build_frontend_subscription_url(  # noqa: SLF001
        status=status,
        provider="vnpay",
        order_code=payment.order_code if payment else None,
        code=rsp_code,
    )
    return RedirectResponse(url=redirect_url, status_code=302)
