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
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.payments.models import PaymentTransaction, PaymentWebhookEvent, SubscriptionPlan
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

DEFAULT_SUBSCRIPTION_PLANS = [
    {"code": "PRO_30D", "name": "Pro 30 ngày", "duration_days": 30, "price_amount": 99000, "sort_order": 1},
    {"code": "PRO_6M", "name": "Pro 6 tháng", "duration_days": 180, "price_amount": 499000, "sort_order": 2},
    {"code": "PRO_1Y", "name": "Pro 1 năm", "duration_days": 365, "price_amount": 899000, "sort_order": 3},
]


class PaymentService:
    @classmethod
    def _stripe_to_plain_data(cls, value: Any) -> Any:
        if hasattr(value, "to_dict_recursive"):
            return cls._stripe_to_plain_data(value.to_dict_recursive())
        if isinstance(value, dict):
            return {str(key): cls._stripe_to_plain_data(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._stripe_to_plain_data(item) for item in value]
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    @classmethod
    async def _sync_stripe_payment_from_session(
        cls,
        db: AsyncSession,
        *,
        payment: PaymentTransaction,
        session_payload: dict[str, Any],
    ) -> PaymentTransaction:
        amount_total = int(session_payload.get("amount_total") or 0)
        currency = str(session_payload.get("currency") or "").upper()
        payment_status = str(session_payload.get("payment_status") or "")
        session_status = str(session_payload.get("status") or "")

        if amount_total != payment.amount or currency != payment.currency:
            return await cls.mark_payment_failed(
                db,
                payment=payment,
                reason="Stripe amount or currency mismatch",
                provider_payload=session_payload,
            )
        if payment_status == "paid":
            return await cls.mark_payment_paid(
                db,
                payment=payment,
                external_transaction_id=str(session_payload.get("payment_intent") or ""),
                provider_payload=session_payload,
                paid_at=datetime.now(timezone.utc),
            )
        if session_status == "expired":
            return await cls.mark_payment_failed(
                db,
                payment=payment,
                reason="Stripe checkout session expired",
                provider_payload=session_payload,
                status="expired",
            )
        return payment

    @staticmethod
    async def ensure_default_subscription_plans(db: AsyncSession) -> None:
        for item in DEFAULT_SUBSCRIPTION_PLANS:
            existing = (
                await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == item["code"]))
            ).scalar_one_or_none()
            if existing is None:
                db.add(SubscriptionPlan(currency="VND", is_active=True, **item))
        await db.flush()

    @classmethod
    async def list_active_subscription_plans(cls, db: AsyncSession) -> list[SubscriptionPlan]:
        await cls.ensure_default_subscription_plans(db)
        result = await db.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active.is_(True))
            .order_by(SubscriptionPlan.sort_order, SubscriptionPlan.duration_days)
        )
        return list(result.scalars().all())

    @classmethod
    async def _get_subscription_plan(cls, db: AsyncSession, plan_code: str, *, require_active: bool = True) -> SubscriptionPlan:
        await cls.ensure_default_subscription_plans(db)
        stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == plan_code)
        if require_active:
            stmt = stmt.where(SubscriptionPlan.is_active.is_(True))
        plan = (await db.execute(stmt)).scalar_one_or_none()
        if plan is None:
            raise BadRequestError(f"Unsupported subscription plan: {plan_code}")
        if plan.currency.upper() != "VND":
            raise BadRequestError("Only VND subscription plans are supported.")
        return plan

    @classmethod
    async def quote_checkout(cls, db: AsyncSession, *, plan_code: str) -> dict[str, Any]:
        plan = await cls._get_subscription_plan(db, plan_code)
        return {
            "plan": plan,
            "amount": plan.price_amount,
            "currency": plan.currency.upper(),
        }

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

    @classmethod
    async def get_payment_for_user(
        cls,
        db: AsyncSession,
        *,
        user: User,
        order_code: str,
    ) -> PaymentTransaction:
        payment = await cls._get_payment_by_order_code(db, order_code)
        if payment is None or payment.user_id != user.id:
            raise NotFoundError("Payment transaction not found.")
        if payment.provider == "stripe" and payment.status == "pending" and payment.external_checkout_id:
            session_payload = cls._stripe_to_plain_data(
                cls._retrieve_stripe_checkout_session(payment.external_checkout_id)
            )
            payment = await cls._sync_stripe_payment_from_session(
                db,
                payment=payment,
                session_payload=session_payload,
            )
            await db.commit()
            await db.refresh(payment)
        return payment

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
        duration_days: int,
        activated_at: datetime,
    ) -> Subscription:
        subscription = await cls._get_subscription_for_user(db, user_id)
        base_start = activated_at
        if subscription and subscription.expires_at and subscription.expires_at > activated_at:
            base_start = subscription.expires_at

        expires_at = base_start + timedelta(days=max(duration_days, 1))
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
            duration_days=payment.duration_days or 30,
            activated_at=paid_at,
        )

        payment.status = "paid"
        payment.paid_at = paid_at
        payment.expires_at = subscription.expires_at
        payment.external_transaction_id = external_transaction_id or payment.external_transaction_id
        payment.provider_payload = provider_payload
        payment.failure_reason = None
        await NotificationService.create_system_notification(
            db,
            user_id=payment.user_id,
            title="VIP activated",
            body=f"Your Pro subscription is active until {subscription.expires_at.strftime('%Y-%m-%d') if subscription.expires_at else 'soon'}.",
        )
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
                            "name": f"AI Talk Practice {payment.plan_code or payment.plan}",
                            "description": f"{payment.duration_days or 30}-day Pro subscription upgrade",
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
                "plan_code": payment.plan_code or "",
                "duration_days": str(payment.duration_days or ""),
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
        if provider != "stripe":
            raise BadRequestError(f"Unsupported payment provider: {provider}")
        plan_code = (body.plan_code or "PRO_30D").strip().upper()
        quote = await cls.quote_checkout(db, plan_code=plan_code)
        subscription_plan: SubscriptionPlan = quote["plan"]

        payment = PaymentTransaction(
            user_id=user.id,
            provider=provider,
            plan=plan,
            plan_code=subscription_plan.code,
            duration_days=subscription_plan.duration_days,
            amount=quote["amount"],
            currency=quote["currency"],
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

        event_object = cls._stripe_to_plain_data(event.get("data", {}).get("object", {}))
        checkout_id = str(event_object.get("id") or "")
        payment = None
        session_payload: dict[str, Any] = event_object
        order_code = ""

        if checkout_id:
            payment = await cls._get_payment_by_checkout_id(db, checkout_id)

        if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
            try:
                if not checkout_id:
                    raise BadRequestError("Stripe webhook missing checkout session id.")

                session_payload = cls._stripe_to_plain_data(cls._retrieve_stripe_checkout_session(checkout_id))
                metadata = session_payload.get("metadata") or {}
                order_code = str(metadata.get("payment_order_code") or "")
                if payment is None and order_code:
                    payment = await cls._get_payment_by_order_code(db, order_code)
                if payment is None:
                    raise NotFoundError("Payment transaction not found for Stripe session.")

                synced_payment = await cls._sync_stripe_payment_from_session(
                    db,
                    payment=payment,
                    session_payload=session_payload,
                )
                if synced_payment.status == "pending":
                    await cls.mark_payment_failed(
                        db,
                        payment=synced_payment,
                        reason=f"Stripe payment status is `{session_payload.get('payment_status') or ''}`",
                        provider_payload=session_payload,
                    )
            except Exception:
                logger.exception(
                    "Stripe webhook processing failed event_id=%s event_type=%s checkout_id=%s order_code=%s",
                    event_id,
                    event_type,
                    checkout_id,
                    order_code,
                )
                raise

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


