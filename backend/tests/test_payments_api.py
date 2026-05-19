from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.security import create_access_token
from app.modules.payments.models import PaymentTransaction
from app.modules.payments.services.payment_service import PaymentService
from app.modules.users.models.subscription import Subscription

class FakeStripeObject:
    def __init__(self, data):
        self.data = data

    def to_dict_recursive(self):
        return self.data

class FakeStripeDataObject:
    def __init__(self, data):
        self._data = data


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
        json={"provider": "stripe", "plan": "PRO", "plan_code": "PRO_30D"},
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
    assert payment.plan_code == "PRO_30D"
    assert payment.duration_days == 30
    assert payment.amount == 99000
    assert payment.currency == "VND"

@pytest.mark.asyncio
async def test_stripe_webhook_marks_payment_paid_and_upgrades_subscription(client, db_session, test_user, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")

    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        plan_code="PRO_30D",
        duration_days=30,
        amount=99000,
        currency="VND",
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
        return FakeStripeDataObject(
            {
                "id": "evt_test_123",
                "type": "checkout.session.completed",
                "data": {"object": FakeStripeDataObject({"id": "cs_test_123", "metadata": {"nested": ["value"]}})},
            }
        )

    def fake_retrieve(cls, checkout_id):
        assert checkout_id == "cs_test_123"
        return FakeStripeDataObject(
            {
                "id": "cs_test_123",
                "metadata": {"payment_order_code": payment.order_code},
                "amount_total": 99000,
                "currency": "vnd",
                "payment_status": "paid",
                "payment_intent": "pi_test_123",
                "line_items": [{"price": FakeStripeDataObject({"id": "price_test_123"})}],
            }
        )

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

@pytest.mark.asyncio
async def test_get_payment_status_reconciles_paid_stripe_session(client, db_session, test_user, monkeypatch):
    token = create_access_token(user_id=test_user.id)

    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        plan_code="PRO_30D",
        duration_days=30,
        amount=99000,
        currency="VND",
        status="pending",
        order_code="ORDERRECONCILE001",
        external_checkout_id="cs_reconcile_123",
        provider_payload={},
    )
    db_session.add(payment)
    await db_session.commit()

    def fake_retrieve(cls, checkout_id):
        assert checkout_id == "cs_reconcile_123"
        return FakeStripeDataObject(
            {
                "id": "cs_reconcile_123",
                "metadata": {"payment_order_code": payment.order_code},
                "amount_total": 99000,
                "currency": "vnd",
                "payment_status": "paid",
                "payment_intent": "pi_reconcile_123",
            }
        )

    monkeypatch.setattr(PaymentService, "_retrieve_stripe_checkout_session", classmethod(fake_retrieve))

    response = await client.get(
        f"/api/payments/transactions/{payment.order_code}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["order_code"] == payment.order_code
    assert data["status"] == "paid"

    await db_session.refresh(payment)
    assert payment.status == "paid"
    assert payment.external_transaction_id == "pi_reconcile_123"

    subscription = (
        await db_session.execute(select(Subscription).where(Subscription.user_id == test_user.id))
    ).scalar_one()
    assert subscription.tier == "PRO"
    assert subscription.status == "active"

@pytest.mark.asyncio
async def test_get_payment_status_keeps_pending_when_stripe_session_payload_is_invalid(
    client,
    db_session,
    test_user,
    monkeypatch,
):
    token = create_access_token(user_id=test_user.id)

    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        plan_code="PRO_30D",
        duration_days=30,
        amount=99000,
        currency="VND",
        status="pending",
        order_code="ORDERINVALIDSESSION001",
        external_checkout_id="cs_invalid_123",
        provider_payload={},
    )
    db_session.add(payment)
    await db_session.commit()

    def fake_retrieve(cls, checkout_id):
        assert checkout_id == "cs_invalid_123"
        return object()

    monkeypatch.setattr(PaymentService, "_retrieve_stripe_checkout_session", classmethod(fake_retrieve))

    response = await client.get(
        f"/api/payments/transactions/{payment.order_code}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["order_code"] == payment.order_code
    assert data["status"] == "pending"

    await db_session.refresh(payment)
    assert payment.status == "pending"

@pytest.mark.asyncio
async def test_get_payment_status_returns_only_current_user_payment(client, db_session, test_user):
    token = create_access_token(user_id=test_user.id)

    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        plan_code="PRO_30D",
        duration_days=30,
        amount=99000,
        currency="VND",
        status="paid",
        order_code="ORDERSTATUS001",
        external_checkout_id="cs_status_123",
        external_transaction_id="pi_status_123",
        provider_payload={},
        paid_at=datetime(2026, 4, 7, tzinfo=timezone.utc),
        expires_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
    )
    db_session.add(payment)
    await db_session.commit()

    response = await client.get(
        f"/api/payments/transactions/{payment.order_code}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["order_code"] == payment.order_code
    assert data["status"] == "paid"
    assert data["plan"] == "PRO"
