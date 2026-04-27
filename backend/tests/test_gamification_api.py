from datetime import date, datetime, timedelta, timezone

import pytest

from app.modules.curriculum.models import LearningLevel, Lesson, LessonExercise, UserExerciseProgress
from app.modules.gamification.models.daily_checkin import DailyCheckin
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User
from app.core.security import hash_password


async def _seed_reward_lesson(db_session, *, xp_reward=50, coin_reward=2):
    level = LearningLevel(code="a1", title="A1", order_index=0)
    db_session.add(level)
    await db_session.flush()
    lesson = Lesson(
        level_id=level.id,
        title="Reward lesson",
        order_index=0,
        xp_reward=xp_reward,
        coin_reward=coin_reward,
    )
    db_session.add(lesson)
    await db_session.flush()
    exercise = LessonExercise(
        lesson_id=lesson.id,
        type="cloze_dictation",
        title="Cloze",
        order_index=0,
        content={"passage": "I drink ___.", "blanks": [{"answer": "coffee"}]},
        pass_score=80,
    )
    db_session.add(exercise)
    await db_session.commit()
    return lesson, exercise


@pytest.mark.asyncio
async def test_gamification_dashboard_initializes_simple_defaults(test_client):
    response = await test_client.get("/api/gamification/me")

    assert response.status_code == 200
    body = response.json()
    assert body["xp"]["total"] == 0
    assert body["xp"]["today"] == 0
    assert body["xp"]["level"] == 1
    assert body["xp"]["level_progress"] == 0
    assert body["xp"]["level_size"] == 100
    assert body["coin"]["balance"] == 0
    assert body["check_in"]["checked_in_today"] is False
    assert body["check_in"]["today_coin_reward"] == 1


@pytest.mark.asyncio
async def test_lesson_completion_awards_configured_xp_coin_once(test_client, db_session, test_user):
    _, exercise = await _seed_reward_lesson(db_session, xp_reward=75, coin_reward=6)

    response = await test_client.post(
        f"/api/exercises/{exercise.id}/attempt",
        json={"answer": {"blanks": ["coffee"]}},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["lesson_completed"] is True
    assert body["reward"]["reward"]["xp_earned"] == 75
    assert body["reward"]["reward"]["coin_earned"] == 6
    assert body["reward"]["dashboard"]["xp"]["total"] == 75
    assert body["reward"]["dashboard"]["coin"]["balance"] == 6

    retry = await test_client.post(
        f"/api/exercises/{exercise.id}/attempt",
        json={"answer": {"blanks": ["coffee"]}},
    )
    assert retry.status_code == 201
    assert retry.json()["reward"] is None
    user = await db_session.get(User, test_user.id)
    assert user.total_xp == 75
    assert user.coin_balance == 6


@pytest.mark.asyncio
async def test_level_curve_and_level_coin_rewards(test_client, admin_client, db_session, test_user):
    _, exercise = await _seed_reward_lesson(db_session, xp_reward=250, coin_reward=0)
    settings = await admin_client.put(
        "/api/admin/gamification/settings",
        json={"level_coin_rewards": {"2": 10, "3": 20}, "reason": "level rewards"},
    )
    assert settings.status_code == 200

    response = await test_client.post(
        f"/api/exercises/{exercise.id}/attempt",
        json={"answer": {"blanks": ["coffee"]}},
    )

    assert response.status_code == 201
    reward = response.json()["reward"]["reward"]
    dashboard = response.json()["reward"]["dashboard"]
    assert reward["levels_gained"] == 2
    assert reward["level_coin_reward"] == 30
    assert dashboard["xp"]["level"] == 3
    assert dashboard["xp"]["level_progress"] == 50
    assert dashboard["xp"]["level_size"] == 100
    assert dashboard["coin"]["balance"] == 30


@pytest.mark.asyncio
async def test_daily_checkin_default_duplicate_and_admin_tier_rewards(
    test_client,
    admin_client,
    db_session,
    test_user,
):
    first = await test_client.post("/api/gamification/check-in")
    assert first.status_code == 200
    assert first.json()["coin_earned"] == 1
    assert first.json()["streak_day"] == 1

    duplicate = await test_client.post("/api/gamification/check-in")
    assert duplicate.status_code == 400

    today = date.today()
    checkin = (
        await db_session.execute(
            DailyCheckin.__table__.select().where(DailyCheckin.user_id == test_user.id)
        )
    ).first()
    await db_session.execute(
        DailyCheckin.__table__.update()
        .where(DailyCheckin.id == checkin.id)
        .values(date=today - timedelta(days=1), streak_day=1)
    )
    await db_session.commit()

    update = await admin_client.put(
        "/api/admin/gamification/settings",
        json={"daily_checkin_coin_rewards": {"1": 1, "2": 3}, "reason": "checkin tiers"},
    )
    assert update.status_code == 200

    second = await test_client.post("/api/gamification/check-in")
    assert second.status_code == 200
    assert second.json()["streak_day"] == 2
    assert second.json()["coin_earned"] == 3


@pytest.mark.asyncio
async def test_missed_checkin_day_resets_streak(test_client, db_session, test_user):
    db_session.add(
        DailyCheckin(
            user_id=test_user.id,
            date=date.today() - timedelta(days=2),
            streak_day=5,
            coin_earned=5,
        )
    )
    await db_session.commit()

    response = await test_client.post("/api/gamification/check-in")

    assert response.status_code == 200
    assert response.json()["streak_day"] == 1
    assert response.json()["coin_earned"] == 1


@pytest.mark.asyncio
async def test_shop_pro_ticket_purchase_requires_and_spends_coin(test_client, db_session, test_user):
    poor = await test_client.post("/api/gamification/shop/purchase", json={"item_code": "pro_1_day_ticket"})
    assert poor.status_code == 400

    user = await db_session.get(User, test_user.id)
    user.coin_balance = 500
    await db_session.commit()

    purchase = await test_client.post("/api/gamification/shop/purchase", json={"item_code": "pro_1_day_ticket"})

    assert purchase.status_code == 200
    body = purchase.json()
    assert body["coin_spent"] == 500
    assert body["dashboard"]["coin"]["balance"] == 0
    assert body["subscription_expires_at"] is not None
    refreshed = await db_session.get(User, test_user.id)
    assert refreshed.subscription.tier == "PRO"
    assert refreshed.subscription.status == "active"


@pytest.mark.asyncio
async def test_speaking_session_start_does_not_require_gamification_currency(test_client, test_scenario):
    response = await test_client.post(
        "/api/sessions",
        json={"scenario_id": test_scenario.id},
    )

    assert response.status_code == 201


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
        preferences={"is_admin": False},
    )
    db_session.add(competitor)
    await db_session.flush()
    db_session.add(Subscription(user_id=competitor.id, tier="FREE", status="active"))

    test_user.total_xp = 1200

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
