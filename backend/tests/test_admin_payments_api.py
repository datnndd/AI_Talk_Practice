from __future__ import annotations

import pytest
from sqlalchemy import select

from app.modules.payments.models import PaymentTransaction
from app.modules.users.models.subscription import Subscription


@pytest.mark.asyncio
async def test_admin_can_list_payment_transactions(admin_client, db_session, test_user):
    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        amount=9900,
        currency="USD",
        status="pending",
        order_code="ADMINPAY001",
        external_checkout_id="cs_admin_001",
        provider_payload={},
    )
    db_session.add(payment)
    await db_session.commit()

    response = await admin_client.get("/api/admin/payments/transactions")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["order_code"] == "ADMINPAY001" for item in data["items"])


@pytest.mark.asyncio
async def test_admin_can_approve_payment_and_activate_subscription(admin_client, db_session, test_user):
    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        amount=9900,
        currency="USD",
        status="pending",
        order_code="ADMINAPPROVE001",
        external_checkout_id="cs_admin_approve_001",
        provider_payload={},
    )
    db_session.add(payment)
    await db_session.commit()

    response = await admin_client.post(
        f"/api/admin/payments/transactions/{payment.id}/approve",
        json={"reason": "Support verified bank transfer"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "paid"

    await db_session.refresh(payment)
    assert payment.status == "paid"

    subscription = (
        await db_session.execute(select(Subscription).where(Subscription.user_id == test_user.id))
    ).scalar_one()
    assert subscription.tier == "PRO"
    assert subscription.status == "active"


@pytest.mark.asyncio
async def test_admin_can_cancel_pending_payment(admin_client, db_session, test_user):
    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        amount=9900,
        currency="USD",
        status="pending",
        order_code="ADMINCANCEL001",
        external_checkout_id="cs_admin_cancel_001",
        provider_payload={},
    )
    db_session.add(payment)
    await db_session.commit()

    response = await admin_client.post(
        f"/api/admin/payments/transactions/{payment.id}/cancel",
        json={"reason": "Customer requested cancellation"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_admin_payment_routes_forbid_non_admin(test_client, db_session, test_user):
    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        amount=9900,
        currency="USD",
        status="pending",
        order_code="ADMINFORBID001",
        external_checkout_id="cs_admin_forbid_001",
        provider_payload={},
    )
    db_session.add(payment)
    await db_session.commit()

    response = await test_client.get("/api/admin/payments/transactions")
    assert response.status_code == 403

    response = await test_client.post(
        f"/api/admin/payments/transactions/{payment.id}/approve",
        json={"reason": "No access"},
    )
    assert response.status_code == 403
