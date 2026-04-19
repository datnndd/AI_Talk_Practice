from datetime import datetime, timedelta, timezone

import pytest

from app.modules.users.models.user import User


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
