from datetime import date, datetime, timedelta, timezone

import pytest

from app.modules.gamification.models.coin_transaction import CoinTransaction
from app.modules.gamification.models.daily_checkin import DailyCheckin
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.sessions.models.session import Session
from app.modules.users.models.user import User


@pytest.mark.asyncio
async def test_admin_user_detail_includes_gamification_and_admin_coin_adjustment(
    admin_client,
    db_session,
    test_user,
):
    user = await db_session.get(User, test_user.id)
    user.total_xp = 250
    user.coin_balance = 20
    await db_session.commit()

    detail = await admin_client.get(f"/api/admin/users/{test_user.id}")
    assert detail.status_code == 200
    gamification = detail.json()["gamification"]
    assert gamification["xp"]["total"] == 250
    assert gamification["xp"]["level"] == 3
    assert gamification["coin"]["balance"] == 20

    adjustment = await admin_client.post(
        f"/api/admin/users/{test_user.id}/gamification/adjust-balance",
        json={"coin_delta": 15, "reason": "support credit"},
    )
    assert adjustment.status_code == 200
    assert adjustment.json()["gamification"]["coin"]["balance"] == 35

    transactions = (
        await db_session.execute(
            CoinTransaction.__table__.select().where(CoinTransaction.user_id == test_user.id)
        )
    ).all()
    assert any(row.type == "admin_adjustment" and row.amount == 15 for row in transactions)

    audit = await admin_client.get("/api/admin/audit-logs")
    assert audit.status_code == 200
    actions = [item["action"] for item in audit.json()["items"]]
    assert "user.balance_adjusted" in actions


@pytest.mark.asyncio
async def test_admin_gamification_settings_manage_level_and_checkin_coin_rewards(
    admin_client,
):
    defaults = await admin_client.get("/api/admin/gamification/settings")
    assert defaults.status_code == 200
    assert defaults.json()["level_coin_rewards"] == {}
    assert defaults.json()["daily_checkin_coin_rewards"]["1"] == 1

    update = await admin_client.put(
        "/api/admin/gamification/settings",
        json={
            "level_coin_rewards": {"2": 10},
            "daily_checkin_coin_rewards": {"1": 1, "3": 5},
            "reason": "balance test",
        },
    )
    assert update.status_code == 200
    assert update.json()["level_coin_rewards"]["2"] == 10
    assert update.json()["daily_checkin_coin_rewards"]["3"] == 5


@pytest.mark.asyncio
async def test_admin_gamification_overview_counts_daily_metrics(
    admin_client,
    db_session,
    test_user,
    test_admin_user,
    test_scenario,
):
    today = date(2026, 4, 19)
    db_session.add_all(
        [
            DailyStat(user_id=test_user.id, date=today, lessons_completed=2, speaking_lessons_completed=1),
            DailyCheckin(user_id=test_user.id, date=today, streak_day=1, coin_earned=1),
            Session(
                user_id=test_user.id,
                scenario_id=test_scenario.id,
                status="completed",
                started_at=datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc),
            ),
        ]
    )
    user = await db_session.get(User, test_user.id)
    user.coin_balance = 25
    admin = await db_session.get(User, test_admin_user.id)
    admin.coin_balance = 75
    await db_session.commit()

    response = await admin_client.get("/api/admin/gamification/overview", params={"date": str(today)})
    assert response.status_code == 200
    body = response.json()
    assert body["active_users_today"] == 1
    assert body["checkins_today"] == 1
    assert body["coins_in_circulation"] == 100
    assert body["pro_upgrade_rate"] == 0.5


@pytest.mark.asyncio
async def test_admin_notifications_support_broadcast_direct_read_state(
    admin_client,
    test_client,
    test_user,
):
    broadcast = await admin_client.post(
        "/api/admin/notifications",
        json={"audience": "all", "title": "System", "body": "New practice challenge"},
    )
    assert broadcast.status_code == 201

    direct = await admin_client.post(
        "/api/admin/notifications",
        json={
            "audience": "users",
            "recipient_user_ids": [test_user.id],
            "title": "Support",
            "body": "Your Coin balance was updated",
        },
    )
    assert direct.status_code == 201

    inbox = await test_client.get("/api/notifications")
    assert inbox.status_code == 200
    items = inbox.json()["items"]
    assert {item["title"] for item in items} == {"System", "Support"}
    assert all(item["read_at"] is None for item in items)

    read = await test_client.post(f"/api/notifications/{items[0]['id']}/read")
    assert read.status_code == 200
    assert read.json()["read_at"] is not None
