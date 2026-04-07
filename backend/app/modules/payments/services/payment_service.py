from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlencode
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

VN_TZ = timezone(timedelta(hours=7))

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
    def _build_query_string(params: dict[str, Any]) -> str:
        items = sorted(
            (key, value)
            for key, value in params.items()
            if value is not None and value != ""
        )
        return "&".join(
            f"{quote(str(key), safe='')}={quote(str(value), safe='')}"
            for key, value in items
        )

    @classmethod
    def _sign_vnpay_params(cls, params: dict[str, Any]) -> str:
        signing_params = {
            key: value
            for key, value in params.items()
            if key not in {"vnp_SecureHash", "vnp_SecureHashType"} and value is not None and value != ""
        }
        query = cls._build_query_string(signing_params)
        return hmac.new(
            (settings.vnpay_hash_secret or "").encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha512,
        ).hexdigest()

    @staticmethod
    def _payment_amount_for(provider: str, plan: str) -> tuple[int, str]:
        if plan not in PLAN_CONFIG:
            raise BadRequestError(f"Unsupported subscription plan: {plan}")

        if provider == "stripe":
            return settings.payment_pro_amount_usd_cents, "USD"
        if provider == "vnpay":
            return settings.payment_pro_amount_vnd, "VND"
        raise BadRequestError(f"Unsupported payment provider: {provider}")

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
    def _normalize_client_ip(client_ip: str | None) -> str:
        if not client_ip:
            return "127.0.0.1"
        if "," in client_ip:
            return client_ip.split(",")[0].strip()
        return client_ip.strip() or "127.0.0.1"

    @staticmethod
    def _load_stripe():
        try:
            import stripe  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on environment
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
    async def _mark_payment_paid(
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
    async def _mark_payment_failed(
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
    def _create_vnpay_payment_url(
        cls,
        *,
        payment: PaymentTransaction,
        body: PaymentCheckoutRequest,
        client_ip: str,
    ) -> dict[str, Any]:
        if not settings.vnpay_tmn_code or not settings.vnpay_hash_secret:
            raise RuntimeError("VNPay is not configured. Missing VNPAY_TMN_CODE or VNPAY_HASH_SECRET.")

        now = datetime.now(VN_TZ)
        expires_at = now + timedelta(minutes=15)
        params: dict[str, Any] = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": settings.vnpay_tmn_code,
            "vnp_Amount": payment.amount * 100,
            "vnp_CurrCode": "VND",
            "vnp_TxnRef": payment.order_code,
            "vnp_OrderInfo": f"Upgrade AI Talk Practice {payment.plan}",
            "vnp_OrderType": "other",
            "vnp_Locale": body.locale or "vn",
            "vnp_ReturnUrl": f"{settings.backend_public_url.rstrip('/')}{settings.vnpay_return_path}",
            "vnp_IpAddr": cls._normalize_client_ip(client_ip),
            "vnp_CreateDate": now.strftime("%Y%m%d%H%M%S"),
            "vnp_ExpireDate": expires_at.strftime("%Y%m%d%H%M%S"),
        }
        if body.bank_code:
            params["vnp_BankCode"] = body.bank_code

        secure_hash = cls._sign_vnpay_params(params)
        query = cls._build_query_string(params)
        checkout_url = f"{settings.vnpay_payment_url}?{query}&vnp_SecureHash={secure_hash}"

        return {
            "checkout_url": checkout_url,
            "external_checkout_id": payment.order_code,
            "provider_payload": {
                "request": params,
            },
            "expires_at": expires_at.astimezone(timezone.utc),
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

        if provider == "stripe":
            checkout = await cls._create_stripe_checkout_session(payment=payment, user=user)
        else:
            checkout = cls._create_vnpay_payment_url(
                payment=payment,
                body=body,
                client_ip=client_ip or "127.0.0.1",
            )

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
    async def process_vnpay_response(
        cls,
        db: AsyncSession,
        *,
        query_params: dict[str, Any],
    ) -> tuple[PaymentTransaction | None, bool, str]:
        secure_hash = query_params.get("vnp_SecureHash")
        if not secure_hash:
            return None, False, "97"

        expected_hash = cls._sign_vnpay_params(query_params)
        if not hmac.compare_digest(secure_hash, expected_hash):
            return None, False, "97"

        order_code = str(query_params.get("vnp_TxnRef") or "")
        if not order_code:
            return None, False, "99"

        payment = await cls._get_payment_by_order_code(db, order_code)
        if payment is None:
            return None, False, "01"

        returned_amount = int(str(query_params.get("vnp_Amount") or "0"))
        if returned_amount != payment.amount * 100:
            await cls._mark_payment_failed(
                db,
                payment=payment,
                reason="VNPay amount mismatch",
                provider_payload=query_params,
            )
            await db.commit()
            return payment, False, "04"

        response_code = str(query_params.get("vnp_ResponseCode") or "")
        transaction_status = str(query_params.get("vnp_TransactionStatus") or response_code)
        if response_code == "00" and transaction_status == "00":
            paid_at_raw = str(query_params.get("vnp_PayDate") or "")
            try:
                paid_at = (
                    datetime.strptime(paid_at_raw, "%Y%m%d%H%M%S")
                    .replace(tzinfo=VN_TZ)
                    .astimezone(timezone.utc)
                    if paid_at_raw
                    else datetime.now(timezone.utc)
                )
            except ValueError:
                paid_at = datetime.now(timezone.utc)

            await cls._mark_payment_paid(
                db,
                payment=payment,
                external_transaction_id=str(query_params.get("vnp_TransactionNo") or ""),
                provider_payload=query_params,
                paid_at=paid_at,
            )
            await db.commit()
            return payment, True, "00"

        await cls._mark_payment_failed(
            db,
            payment=payment,
            reason=f"VNPay payment failed with response code {response_code or 'unknown'}",
            provider_payload=query_params,
            status="cancelled" if response_code in {"24"} else "failed",
        )
        await db.commit()
        return payment, False, response_code or "99"

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
                await cls._mark_payment_failed(
                    db,
                    payment=payment,
                    reason="Stripe amount or currency mismatch",
                    provider_payload=session_payload,
                )
            elif payment_status == "paid":
                await cls._mark_payment_paid(
                    db,
                    payment=payment,
                    external_transaction_id=str(session_payload.get("payment_intent") or ""),
                    provider_payload=session_payload,
                    paid_at=datetime.now(timezone.utc),
                )
            else:
                await cls._mark_payment_failed(
                    db,
                    payment=payment,
                    reason=f"Stripe payment status is `{payment_status}`",
                    provider_payload=session_payload,
                )

        elif event_type in {"checkout.session.expired", "checkout.session.async_payment_failed"}:
            if payment is not None:
                await cls._mark_payment_failed(
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
