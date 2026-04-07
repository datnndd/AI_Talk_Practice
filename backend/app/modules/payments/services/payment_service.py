from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.payments.models import PaymentTransaction, PaymentWebhookEvent
from app.modules.payments.schemas.payment import PaymentCheckoutRequest
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User

logger = logging.getLogger(__name__)

PLAN_CONFIG = {
    "PRO": {
        "features": {
            "live_ai_practice": True,
            "advanced_scenarios": True,
            "premium_tutor": True,
        },
    }
}


class PaymentService:
    @staticmethod
    def _payment_amount_for(provider: str, plan: str) -> tuple[int, str]:
        if plan not in PLAN_CONFIG:
            raise BadRequestError(f"Unsupported subscription plan: {plan}")
        if provider != "stripe":
            raise BadRequestError(f"Unsupported payment provider: {provider}")
        return settings.payment_pro_amount_usd_cents, "USD"

    @staticmethod
    def _subscription_duration_days() -> int:
        return max(settings.payment_pro_duration_days, 1)

    @staticmethod
    def _build_frontend_subscription_url(status: str, provider: str, order_code: str | None = None, code: str | None = None) -> str:
        query: dict[str, str] = {
            "payment": status,
            "provider": provider,
        }
        if order_code:
            query["order_code"] = order_code
        if code:
            query["code"] = code
        return f"{settings.frontend_url.rstrip('/')}/subscription?{urlencode(query)}"

    @staticmethod
    def _load_stripe():
        try:
            import stripe  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Stripe SDK is not installed. Add `stripe` to backend dependencies.") from exc

        if not settings.stripe_secret_key:
            raise RuntimeError("Stripe is not configured. Missing STRIPE_SECRET_KEY.")

        stripe.api_key = settings.stripe_secret_key
        return stripe

    @staticmethod
    async def _get_payment_by_order_code(db: AsyncSession, order_code: str) -> PaymentTransaction | None:
        result = await db.execute(
            select(PaymentTransaction).where(PaymentTransaction.order_code == order_code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_payment_by_checkout_id(db: AsyncSession, checkout_id: str) -> PaymentTransaction | None:
        result = await db.execute(
            select(PaymentTransaction).where(PaymentTransaction.external_checkout_id == checkout_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_subscription_for_user(db: AsyncSession, user_id: int) -> Subscription | None:
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def _upsert_subscription(
        cls,
        db: AsyncSession,
        *,
        user_id: int,
        plan: str,
        activated_at: datetime,
    ) -> Subscription:
        subscription = await cls._get_subscription_for_user(db, user_id)
        base_start = activated_at
        if subscription and subscription.expires_at and subscription.expires_at > activated_at:
            base_start = subscription.expires_at

        expires_at = base_start + timedelta(days=cls._subscription_duration_days())
        features = PLAN_CONFIG[plan]["features"]

        if subscription is None:
            subscription = Subscription(
                user_id=user_id,
                tier=plan,
                status="active",
                expires_at=expires_at,
                features=features,
            )
            db.add(subscription)
        else:
            subscription.tier = plan
            subscription.status = "active"
            subscription.expires_at = expires_at
            subscription.features = features

        await db.flush()
        return subscription

    @classmethod
    async def mark_payment_paid(
        cls,
        db: AsyncSession,
        *,
        payment: PaymentTransaction,
        external_transaction_id: str | None,
        provider_payload: dict[str, Any],
        paid_at: datetime,
    ) -> PaymentTransaction:
        if payment.status == "paid":
            return payment

        subscription = await cls._upsert_subscription(
            db,
            user_id=payment.user_id,
            plan=payment.plan,
            activated_at=paid_at,
        )

        payment.status = "paid"
        payment.paid_at = paid_at
        payment.expires_at = subscription.expires_at
        payment.external_transaction_id = external_transaction_id or payment.external_transaction_id
        payment.provider_payload = provider_payload
        payment.failure_reason = None
        await db.flush()
        return payment

    @staticmethod
    async def mark_payment_failed(
        db: AsyncSession,
        *,
        payment: PaymentTransaction,
        reason: str,
        provider_payload: dict[str, Any],
        status: str = "failed",
    ) -> PaymentTransaction:
        if payment.status == "paid":
            return payment

        payment.status = status
        payment.failure_reason = reason
        payment.provider_payload = provider_payload
        await db.flush()
        return payment

    @classmethod
    async def _create_stripe_checkout_session(
        cls,
        *,
        payment: PaymentTransaction,
        user: User,
    ) -> dict[str, Any]:
        stripe = cls._load_stripe()
        success_url = cls._build_frontend_subscription_url(
            status="success",
            provider="stripe",
            order_code=payment.order_code,
        )
        cancel_url = cls._build_frontend_subscription_url(
            status="cancelled",
            provider="stripe",
            order_code=payment.order_code,
        )

        session = stripe.checkout.Session.create(
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=[
                {
                    "price_data": {
                        "currency": payment.currency.lower(),
                        "unit_amount": payment.amount,
                        "product_data": {
                            "name": "AI Talk Practice Pro",
                            "description": "30-day Pro subscription upgrade",
                        },
                    },
                    "quantity": 1,
                }
            ],
            customer_email=user.email,
            client_reference_id=payment.order_code,
            metadata={
                "payment_order_code": payment.order_code,
                "payment_id": str(payment.id),
                "user_id": str(user.id),
                "plan": payment.plan,
            },
        )
        return {
            "checkout_url": session.url,
            "external_checkout_id": session.id,
            "provider_payload": {
                "session_id": session.id,
                "payment_status": getattr(session, "payment_status", None),
            },
            "expires_at": datetime.fromtimestamp(session.expires_at, tz=timezone.utc)
            if getattr(session, "expires_at", None)
            else None,
        }

    @classmethod
    async def create_checkout(
        cls,
        db: AsyncSession,
        *,
        user: User,
        body: PaymentCheckoutRequest,
        client_ip: str | None,
    ) -> PaymentTransaction:
        del client_ip
        provider = body.provider.lower()
        plan = body.plan.upper()
        amount, currency = cls._payment_amount_for(provider, plan)

        payment = PaymentTransaction(
            user_id=user.id,
            provider=provider,
            plan=plan,
            amount=amount,
            currency=currency,
            status="pending",
            order_code=uuid4().hex[:24].upper(),
            provider_payload={},
        )
        db.add(payment)
        await db.flush()

        checkout = await cls._create_stripe_checkout_session(payment=payment, user=user)

        payment.payment_url = checkout["checkout_url"]
        payment.external_checkout_id = checkout.get("external_checkout_id")
        payment.provider_payload = checkout.get("provider_payload")
        payment.expires_at = checkout.get("expires_at")

        await db.commit()
        await db.refresh(payment)
        logger.info(
            "Created %s checkout for user id=%s payment order=%s",
            provider,
            user.id,
            payment.order_code,
        )
        return payment

    @classmethod
    def _construct_stripe_event(cls, payload: bytes, signature: str):
        stripe = cls._load_stripe()
        if not settings.stripe_webhook_secret:
            raise RuntimeError("Stripe webhook is not configured. Missing STRIPE_WEBHOOK_SECRET.")
        return stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)

    @classmethod
    def _retrieve_stripe_checkout_session(cls, checkout_id: str):
        stripe = cls._load_stripe()
        return stripe.checkout.Session.retrieve(checkout_id)

    @staticmethod
    async def _get_processed_event(
        db: AsyncSession,
        *,
        provider: str,
        event_id: str,
    ) -> PaymentWebhookEvent | None:
        result = await db.execute(
            select(PaymentWebhookEvent).where(
                PaymentWebhookEvent.provider == provider,
                PaymentWebhookEvent.event_id == event_id,
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def process_stripe_webhook(
        cls,
        db: AsyncSession,
        *,
        payload: bytes,
        signature: str,
    ) -> dict[str, Any]:
        event = cls._construct_stripe_event(payload, signature)
        event_id = str(event.get("id"))
        event_type = str(event.get("type"))

        if await cls._get_processed_event(db, provider="stripe", event_id=event_id):
            return {"received": True, "duplicate": True}

        event_object = event.get("data", {}).get("object", {})
        checkout_id = str(event_object.get("id") or "")
        payment = None
        session_payload: dict[str, Any] = dict(event_object)

        if checkout_id:
            payment = await cls._get_payment_by_checkout_id(db, checkout_id)

        if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
            if not checkout_id:
                raise BadRequestError("Stripe webhook missing checkout session id.")

            session = cls._retrieve_stripe_checkout_session(checkout_id)
            session_payload = dict(session)
            metadata = session_payload.get("metadata") or {}
            order_code = str(metadata.get("payment_order_code") or "")
            if payment is None and order_code:
                payment = await cls._get_payment_by_order_code(db, order_code)
            if payment is None:
                raise NotFoundError("Payment transaction not found for Stripe session.")

            amount_total = int(session_payload.get("amount_total") or 0)
            currency = str(session_payload.get("currency") or "").upper()
            payment_status = str(session_payload.get("payment_status") or "")
            if amount_total != payment.amount or currency != payment.currency:
                await cls.mark_payment_failed(
                    db,
                    payment=payment,
                    reason="Stripe amount or currency mismatch",
                    provider_payload=session_payload,
                )
            elif payment_status == "paid":
                await cls.mark_payment_paid(
                    db,
                    payment=payment,
                    external_transaction_id=str(session_payload.get("payment_intent") or ""),
                    provider_payload=session_payload,
                    paid_at=datetime.now(timezone.utc),
                )
            else:
                await cls.mark_payment_failed(
                    db,
                    payment=payment,
                    reason=f"Stripe payment status is `{payment_status}`",
                    provider_payload=session_payload,
                )

        elif event_type in {"checkout.session.expired", "checkout.session.async_payment_failed"}:
            if payment is not None:
                await cls.mark_payment_failed(
                    db,
                    payment=payment,
                    reason=f"Stripe event `{event_type}` received",
                    provider_payload=session_payload,
                    status="expired" if event_type == "checkout.session.expired" else "failed",
                )

        db.add(
            PaymentWebhookEvent(
                provider="stripe",
                event_id=event_id,
                event_type=event_type,
                payload=session_payload,
                processed_at=datetime.now(timezone.utc),
                notes="processed",
            )
        )
        await db.commit()

        return {"received": True, "event_type": event_type}
