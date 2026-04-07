from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token
from app.modules.payments.models import PaymentTransaction
from app.modules.payments.services.payment_service import PaymentService
from app.modules.users.models.subscription import Subscription


@pytest.mark.asyncio
async def test_create_stripe_checkout_returns_checkout_url(client, db_session, test_user, monkeypatch):
    token = create_access_token(user_id=test_user.id)

    async def fake_create(cls, *, payment, user):
        return {
            "checkout_url": "https://checkout.stripe.test/session/cs_test_123",
            "external_checkout_id": "cs_test_123",
            "provider_payload": {"session_id": "cs_test_123"},
            "expires_at": datetime(2026, 4, 8, tzinfo=timezone.utc),
        }

    monkeypatch.setattr(
        PaymentService,
        "_create_stripe_checkout_session",
        classmethod(fake_create),
    )

    response = await client.post(
        "/api/payments/checkout",
        json={"provider": "stripe", "plan": "PRO"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "stripe"
    assert data["status"] == "pending"
    assert data["checkout_url"] == "https://checkout.stripe.test/session/cs_test_123"

    payment = (
        await db_session.execute(
            select(PaymentTransaction).where(PaymentTransaction.order_code == data["order_code"])
        )
    ).scalar_one()
    assert payment.external_checkout_id == "cs_test_123"
    assert payment.amount == settings.payment_pro_amount_usd_cents
    assert payment.currency == "USD"


@pytest.mark.asyncio
async def test_create_vnpay_checkout_returns_signed_checkout_url(client, test_user, monkeypatch):
    token = create_access_token(user_id=test_user.id)

    monkeypatch.setattr(settings, "vnpay_tmn_code", "TESTCODE")
    monkeypatch.setattr(settings, "vnpay_hash_secret", "SECRET123")
    monkeypatch.setattr(settings, "backend_public_url", "http://testserver")

    response = await client.post(
        "/api/payments/checkout",
        json={"provider": "vnpay", "plan": "PRO", "locale": "vn"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "vnpay"
    assert "sandbox.vnpayment.vn" in data["checkout_url"]
    assert "vnp_SecureHash=" in data["checkout_url"]
    assert data["currency"] == "VND"


@pytest.mark.asyncio
async def test_vnpay_return_marks_payment_paid_and_upgrades_subscription(client, db_session, test_user, monkeypatch):
    monkeypatch.setattr(settings, "vnpay_hash_secret", "SECRET123")
    monkeypatch.setattr(settings, "frontend_url", "http://frontend.test")

    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="vnpay",
        plan="PRO",
        amount=199000,
        currency="VND",
        status="pending",
        order_code="ORDERVNPAY001",
        provider_payload={},
    )
    db_session.add(payment)
    await db_session.commit()

    params = {
        "vnp_Amount": str(payment.amount * 100),
        "vnp_BankCode": "NCB",
        "vnp_OrderInfo": "Upgrade",
        "vnp_ResponseCode": "00",
        "vnp_TmnCode": "TESTCODE",
        "vnp_TransactionNo": "14123456",
        "vnp_TransactionStatus": "00",
        "vnp_TxnRef": payment.order_code,
        "vnp_PayDate": "20260407093000",
    }
    params["vnp_SecureHash"] = PaymentService._sign_vnpay_params(params)

    response = await client.get("/api/payments/vnpay/return", params=params, follow_redirects=False)

    assert response.status_code == 302
    assert "payment=success" in response.headers["location"]

    await db_session.refresh(payment)
    assert payment.status == "paid"
    assert payment.external_transaction_id == "14123456"

    subscription = (
        await db_session.execute(select(Subscription).where(Subscription.user_id == test_user.id))
    ).scalar_one()
    assert subscription.tier == "PRO"
    assert subscription.status == "active"
    assert subscription.features["live_ai_practice"] is True


@pytest.mark.asyncio
async def test_stripe_webhook_marks_payment_paid_and_upgrades_subscription(client, db_session, test_user, monkeypatch):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")

    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        amount=settings.payment_pro_amount_usd_cents,
        currency="USD",
        status="pending",
        order_code="ORDERSTRIPE001",
        external_checkout_id="cs_test_123",
        provider_payload={},
    )
    db_session.add(payment)
    await db_session.commit()

    def fake_construct(cls, payload, signature):
        assert payload == b"{}"
        assert signature == "sig_test"
        return {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_123"}},
        }

    def fake_retrieve(cls, checkout_id):
        assert checkout_id == "cs_test_123"
        return {
            "id": "cs_test_123",
            "metadata": {"payment_order_code": payment.order_code},
            "amount_total": settings.payment_pro_amount_usd_cents,
            "currency": "usd",
            "payment_status": "paid",
            "payment_intent": "pi_test_123",
        }

    monkeypatch.setattr(PaymentService, "_construct_stripe_event", classmethod(fake_construct))
    monkeypatch.setattr(PaymentService, "_retrieve_stripe_checkout_session", classmethod(fake_retrieve))

    response = await client.post(
        "/api/payments/stripe/webhook",
        content=b"{}",
        headers={"stripe-signature": "sig_test"},
    )

    assert response.status_code == 200
    assert response.json()["received"] is True

    await db_session.refresh(payment)
    assert payment.status == "paid"
    assert payment.external_transaction_id == "pi_test_123"

    subscription = (
        await db_session.execute(select(Subscription).where(Subscription.user_id == test_user.id))
    ).scalar_one()
    assert subscription.tier == "PRO"
    assert subscription.status == "active"
