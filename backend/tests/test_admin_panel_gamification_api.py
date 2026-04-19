from datetime import date, datetime, timedelta, timezone

import pytest

from app.modules.gamification.models.achievement import Achievement
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.gamification.models.gem_transaction import GemTransaction
from app.modules.gamification.models.user_achievement import UserAchievement
from app.modules.sessions.models.session import Session
from app.modules.users.models.user import User


@pytest.mark.asyncio
async def test_admin_user_detail_includes_gamification_and_admin_actions(
    admin_client,
    db_session,
    test_user,
):
    achievement = Achievement(
        code="manual_badge",
        name="Manual Badge",
        description="Seeded achievement",
        icon_url="badge-manual",
        gem_reward=5,
        condition={"total_xp": 100},
    )
    db_session.add(achievement)
    await db_session.flush()

    user = await db_session.get(User, test_user.id)
    user.current_streak = 5
    user.longest_streak = 8
    user.last_completed_lesson_date = date.today()
    user.total_xp = 1250
    user.gem_balance = 20
    user.heart_balance = 3
    db_session.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
    await db_session.commit()

    detail = await admin_client.get(f"/api/admin/users/{test_user.id}")
    assert detail.status_code == 200
    gamification = detail.json()["gamification"]
    assert gamification["streak"]["current"] == 5
    assert gamification["xp"]["total"] == 1250
    assert gamification["xp"]["level"] == 2
    assert gamification["gem"]["balance"] == 20
    assert gamification["heart"]["current"] == 3
    assert gamification["achievements"]["unlocked"][0]["code"] == "manual_badge"

    reset = await admin_client.post(
        f"/api/admin/users/{test_user.id}/gamification/reset-streak",
        json={"reason": "support request"},
    )
    assert reset.status_code == 200
    assert reset.json()["gamification"]["streak"]["current"] == 0
    assert reset.json()["gamification"]["streak"]["longest"] == 8
    assert reset.json()["gamification"]["streak"]["last_completed_lesson_date"] is None

    adjustment = await admin_client.post(
        f"/api/admin/users/{test_user.id}/gamification/adjust-balance",
        json={"gem_delta": 15, "heart_delta": 1, "reason": "support credit"},
    )
    assert adjustment.status_code == 200
    assert adjustment.json()["gamification"]["gem"]["balance"] == 35
    assert adjustment.json()["gamification"]["heart"]["current"] == 4

    transactions = (
        await db_session.execute(
            GemTransaction.__table__.select().where(GemTransaction.user_id == test_user.id)
        )
    ).all()
    assert any(row.type == "admin_adjustment" and row.amount == 15 for row in transactions)

    audit = await admin_client.get("/api/admin/audit-logs")
    assert audit.status_code == 200
    actions = [item["action"] for item in audit.json()["items"]]
    assert "user.streak_reset" in actions
    assert "user.balance_adjusted" in actions


@pytest.mark.asyncio
async def test_admin_gamification_settings_affect_rewards_and_heart_prices(
    admin_client,
    test_client,
    db_session,
    test_user,
):
    defaults = await admin_client.get("/api/admin/gamification/settings")
    assert defaults.status_code == 200
    assert defaults.json()["xp_by_lesson_type"]["vocabulary"] == 10
    assert defaults.json()["xp_per_gem"] == 10
    assert defaults.json()["heart_purchase_prices"]["1"] == 10
    assert defaults.json()["heart_refill_minutes"] == 60

    update = await admin_client.put(
        "/api/admin/gamification/settings",
        json={
            "xp_by_lesson_type": {"vocabulary": 50},
            "xp_per_gem": 5,
            "heart_purchase_prices": {"1": 7},
            "heart_refill_minutes": 30,
            "reason": "balance test",
        },
    )
    assert update.status_code == 200
    assert update.json()["xp_by_lesson_type"]["vocabulary"] == 50
    assert update.json()["xp_per_gem"] == 5
    assert update.json()["heart_purchase_prices"]["1"] == 7
    assert update.json()["heart_refill_minutes"] == 30

    lesson = await test_client.post(
        "/api/gamification/lessons/complete",
        json={"lesson_type": "vocabulary"},
    )
    assert lesson.status_code == 200
    assert lesson.json()["reward"] == {"xp_earned": 50, "gem_earned": 10}

    user = await db_session.get(User, test_user.id)
    user.gem_balance = 7
    user.heart_balance = 0
    user.last_heart_refill_at = datetime.now(timezone.utc)
    await db_session.commit()

    purchase = await test_client.post("/api/gamification/hearts/purchase", json={"hearts": 1})
    assert purchase.status_code == 200
    assert purchase.json()["gem_spent"] == 7
    assert purchase.json()["dashboard"]["heart"]["current"] == 1

    user = await db_session.get(User, test_user.id)
    user.heart_balance = 0
    user.last_heart_refill_at = datetime.now(timezone.utc) - timedelta(minutes=65)
    await db_session.commit()

    dashboard = await test_client.get("/api/gamification/me")
    assert dashboard.status_code == 200
    assert dashboard.json()["heart"]["current"] == 2


@pytest.mark.asyncio
async def test_admin_can_manage_achievements_and_soft_deleted_do_not_unlock(
    admin_client,
    test_client,
):
    created = await admin_client.post(
        "/api/admin/gamification/achievements",
        json={
            "code": "xp_10_admin",
            "name": "XP Admin",
            "description": "Reach 10 XP",
            "gem_reward": 33,
            "condition": {"total_xp": 10},
            "icon": "badge-admin",
        },
    )
    assert created.status_code == 201
    achievement_id = created.json()["id"]

    updated = await admin_client.patch(
        f"/api/admin/gamification/achievements/{achievement_id}",
        json={"name": "XP Admin Updated", "gem_reward": 44, "is_active": True},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "XP Admin Updated"
    assert updated.json()["gem_reward"] == 44

    deleted = await admin_client.delete(f"/api/admin/gamification/achievements/{achievement_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted_at"] is not None

    lesson = await test_client.post(
        "/api/gamification/lessons/complete",
        json={"lesson_type": "vocabulary"},
    )
    assert lesson.status_code == 200
    assert "xp_10_admin" not in {item["code"] for item in lesson.json()["unlocked_achievements"]}


@pytest.mark.asyncio
async def test_admin_gamification_overview_counts_daily_metrics(
    admin_client,
    db_session,
    test_user,
    test_admin_user,
    test_scenario,
):
    today = date(2026, 4, 19)
    yesterday = today - timedelta(days=1)
    db_session.add_all(
        [
            DailyStat(user_id=test_user.id, date=today, lessons_completed=2, speaking_lessons_completed=1),
            DailyStat(user_id=test_user.id, date=yesterday, lessons_completed=1),
            DailyStat(user_id=test_admin_user.id, date=yesterday, lessons_completed=1),
            Session(
                user_id=test_user.id,
                scenario_id=test_scenario.id,
                status="completed",
                started_at=datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc),
            ),
        ]
    )
    user = await db_session.get(User, test_user.id)
    user.gem_balance = 25
    admin = await db_session.get(User, test_admin_user.id)
    admin.gem_balance = 75
    await db_session.commit()

    response = await admin_client.get("/api/admin/gamification/overview", params={"date": str(today)})
    assert response.status_code == 200
    body = response.json()
    assert body["active_users_today"] == 1
    assert body["speaking_sessions_started"] == 1
    assert body["gems_in_circulation"] == 100
    assert body["pro_upgrade_rate"] == 0.5
    assert body["streak_retention_rate"] == 0.5


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
            "body": "Your Hearts were restored",
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
