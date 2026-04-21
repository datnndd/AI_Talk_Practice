from datetime import datetime, timedelta, timezone

import pytest

from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.users.models.user import User
from app.modules.users.models.subscription import Subscription
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_gamification_dashboard_initializes_simple_defaults(test_client):
    response = await test_client.get("/api/gamification/me")

    assert response.status_code == 200
    body = response.json()
    assert body["streak"]["current"] == 0
    assert body["xp"]["total"] == 0
    assert body["xp"]["today"] == 0
    assert body["xp"]["daily_goal"] == 50
    assert body["xp"]["level"] == 1
    assert body["xp"]["level_progress"] == 0
    assert body["gem"]["balance"] == 0
    assert body["heart"]["current"] == 5
    assert body["heart"]["max"] == 5
    assert body["heart"]["is_unlimited"] is False
    assert {item["code"] for item in body["achievements"]["available"]} >= {
        "first_lesson",
        "streak_7",
        "speaking_10",
    }


@pytest.mark.asyncio
async def test_completing_lesson_awards_xp_gems_streak_and_first_achievement(test_client):
    response = await test_client.post(
        "/api/gamification/lessons/complete",
        json={"lesson_type": "vocabulary"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reward"]["xp_earned"] == 10
    assert body["reward"]["gem_earned"] == 1
    assert body["dashboard"]["xp"]["total"] == 10
    assert body["dashboard"]["xp"]["today"] == 10
    assert body["dashboard"]["gem"]["balance"] == 21
    assert body["dashboard"]["streak"]["current"] == 1
    assert body["unlocked_achievements"] == [
        {
            "code": "first_lesson",
            "name": "Bai hoc dau tien",
            "description": "Hoan thanh 1 bai hoc.",
            "gem_reward": 20,
            "icon": "badge-first-lesson",
            "unlocked_at": body["unlocked_achievements"][0]["unlocked_at"],
        }
    ]


@pytest.mark.asyncio
async def test_free_user_spends_one_heart_when_starting_speaking_session(
    test_client,
    test_scenario,
):
    before = await test_client.get("/api/gamification/me")
    assert before.json()["heart"]["current"] == 5

    response = await test_client.post(
        "/api/sessions",
        json={"scenario_id": test_scenario.id, "mode": "roleplay"},
    )

    assert response.status_code == 201
    after = await test_client.get("/api/gamification/me")
    assert after.json()["heart"]["current"] == 4


@pytest.mark.asyncio
async def test_heart_refills_hourly_and_can_be_bought_with_gems(
    test_client,
    db_session,
    test_user,
):
    user = await db_session.get(User, test_user.id)
    user.heart_balance = 0
    user.gem_balance = 40
    user.last_heart_refill_at = datetime.now(timezone.utc) - timedelta(hours=2, minutes=5)
    await db_session.commit()

    dashboard = await test_client.get("/api/gamification/me")
    assert dashboard.json()["heart"]["current"] == 2

    response = await test_client.post(
        "/api/gamification/hearts/purchase",
        json={"hearts": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["gem_spent"] == 40
    assert body["dashboard"]["gem"]["balance"] == 0
    assert body["dashboard"]["heart"]["current"] == 5


@pytest.mark.asyncio
async def test_pro_user_has_unlimited_hearts_and_sessions_do_not_consume_them(
    admin_client,
    test_scenario,
):
    before = await admin_client.get("/api/gamification/me")
    assert before.json()["heart"]["is_unlimited"] is True
    assert before.json()["heart"]["current"] is None

    response = await admin_client.post(
        "/api/sessions",
        json={"scenario_id": test_scenario.id, "mode": "roleplay"},
    )

    assert response.status_code == 201
    after = await admin_client.get("/api/gamification/me")
    assert after.json()["heart"]["is_unlimited"] is True
    assert after.json()["heart"]["current"] is None


@pytest.mark.asyncio
async def test_leaderboard_returns_real_weekly_and_all_time_data(test_client, db_session, test_user):
    today = datetime.now(timezone.utc).date()

    competitor = User(
        email="leader@example.com",
        password_hash=hash_password("leader123"),
        display_name="Leaderboard Pro",
        native_language="en",
        target_language="de",
        level="advanced",
        total_xp=2000,
        current_streak=9,
        preferences={"is_admin": False},
    )
    db_session.add(competitor)
    await db_session.flush()
    db_session.add(Subscription(user_id=competitor.id, tier="FREE", status="active"))

    test_user.total_xp = 1200
    test_user.current_streak = 4

    db_session.add_all(
        [
            DailyStat(user_id=test_user.id, date=today, xp_earned=120),
            DailyStat(user_id=competitor.id, date=today, xp_earned=280),
        ]
    )
    await db_session.commit()

    weekly_response = await test_client.get("/api/gamification/leaderboard?period=weekly&limit=5")

    assert weekly_response.status_code == 200
    weekly_body = weekly_response.json()
    assert weekly_body["period"] == "weekly"
    assert weekly_body["entries"][0]["display_name"] == "Leaderboard Pro"
    assert weekly_body["entries"][0]["score"] == 280
    assert weekly_body["current_user"]["display_name"] == "Test User"
    assert weekly_body["current_user"]["score"] == 120
    assert weekly_body["current_user"]["rank"] == 2

    all_time_response = await test_client.get("/api/gamification/leaderboard?period=all_time&limit=5")

    assert all_time_response.status_code == 200
    all_time_body = all_time_response.json()
    assert all_time_body["period"] == "all_time"
    assert all_time_body["entries"][0]["display_name"] == "Leaderboard Pro"
    assert all_time_body["entries"][0]["score"] == 2000
    assert all_time_body["current_user"]["score"] == 1200
    assert all_time_body["available_periods"] == ["weekly", "all_time"]
