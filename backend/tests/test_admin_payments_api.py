from __future__ import annotations

import pytest
from sqlalchemy import select

from app.modules.notifications.models.notification import Notification
from app.modules.payments.models import PaymentTransaction
from app.modules.users.models.subscription import Subscription


@pytest.mark.asyncio
async def test_admin_can_list_payment_transactions(admin_client, db_session, test_user):
    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        plan_code="PRO_30D",
        duration_days=30,
        amount=99000,
        currency="VND",
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
        plan_code="PRO_30D",
        duration_days=30,
        amount=99000,
        currency="VND",
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
    notification = (
        await db_session.execute(
            select(Notification).where(
                Notification.recipient_user_id == test_user.id,
                Notification.title == "VIP activated",
            )
        )
    ).scalar_one()
    assert "active until" in notification.body


@pytest.mark.asyncio
async def test_admin_can_cancel_pending_payment(admin_client, db_session, test_user):
    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        plan_code="PRO_30D",
        duration_days=30,
        amount=99000,
        currency="VND",
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
    notification = (
        await db_session.execute(
            select(Notification).where(
                Notification.recipient_user_id == test_user.id,
                Notification.title == "Payment failed",
            )
        )
    ).scalar_one_or_none()
    assert notification is None


@pytest.mark.asyncio
async def test_admin_payment_routes_forbid_non_admin(test_client, db_session, test_user):
    payment = PaymentTransaction(
        user_id=test_user.id,
        provider="stripe",
        plan="PRO",
        plan_code="PRO_30D",
        duration_days=30,
        amount=99000,
        currency="VND",
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

@pytest.mark.asyncio
async def test_admin_can_manage_subscription_plans(admin_client):
    response = await admin_client.get("/api/admin/payments/plans")
    assert response.status_code == 200
    plans = response.json()
    assert {plan["code"] for plan in plans} >= {"PRO_30D", "PRO_6M", "PRO_1Y"}

    response = await admin_client.put(
        "/api/admin/payments/plans/PRO_30D",
        json={"name": "Pro 30 ngày", "price_amount": 129000, "is_active": True, "sort_order": 1},
    )
    assert response.status_code == 200
    assert response.json()["price_amount"] == 129000
    assert response.json()["currency"] == "VND"
