from datetime import date, datetime, timedelta, timezone

import pytest

from app.modules.curriculum.models import LearningSection, Lesson, Unit
from app.modules.gamification.models.daily_checkin import DailyCheckin
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.gamification.models.shop_product import ShopProduct
from app.modules.gamification.models.shop_redemption import ShopRedemption
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User
from app.core.security import hash_password


async def _seed_reward_lesson(db_session, *, xp_reward=50, coin_reward=2):
    section = LearningSection(code="a1", title="A1", order_index=0)
    db_session.add(section)
    await db_session.flush()
    unit = Unit(
        section_id=section.id,
        title="Reward lesson",
        order_index=0,
        xp_reward=xp_reward,
        coin_reward=coin_reward,
    )
    db_session.add(unit)
    await db_session.flush()
    lesson = Lesson(
        unit_id=unit.id,
        type="definition_choice",
        title="Choice",
        order_index=0,
        content={
            "definition_audio_url": "/static/uploads/lesson-audio/coffee.wav",
            "definition_text": "A hot drink.",
            "options": [
                {"word": "coffee", "is_correct": True},
                {"word": "tea", "is_correct": False},
                {"word": "milk", "is_correct": False},
                {"word": "water", "is_correct": False},
            ],
        },
        pass_score=80,
    )
    db_session.add(lesson)
    await db_session.commit()
    return unit, lesson


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
    assert body["check_in"]["current_streak"] == 0
    assert body["check_in"]["today_coin_reward"] == 1
    assert len(body["check_in"]["calendar_days"]) >= 28

@pytest.mark.asyncio
async def test_daily_checkin_duplicate_manual_and_calendar(test_client):
    first = await test_client.post("/api/gamification/check-in")

    assert first.status_code == 200
    today = date.today()
    calendar_today = next(
        day for day in first.json()["dashboard"]["check_in"]["calendar_days"] if day["date"] == today.isoformat()
    )
    assert calendar_today["checked_in"] is True
    assert calendar_today["is_today"] is True
    assert calendar_today["streak_day"] == 1

    duplicate = await test_client.post("/api/gamification/check-in")

    assert duplicate.status_code == 400


@pytest.mark.asyncio
async def test_daily_checkin_continues_streak_from_yesterday(test_client, db_session, test_user):
    db_session.add(DailyCheckin(user_id=test_user.id, date=date.today() - timedelta(days=1), streak_day=4, coin_earned=2))
    await db_session.commit()

    continued = await test_client.post("/api/gamification/check-in")

    assert continued.status_code == 200
    assert continued.json()["streak_day"] == 5

@pytest.mark.asyncio
async def test_lesson_completion_awards_configured_xp_coin_once(test_client, db_session, test_user):
    _, lesson = await _seed_reward_lesson(db_session, xp_reward=75, coin_reward=6)

    response = await test_client.post(
        f"/api/lessons/{lesson.id}/attempt",
        json={"answer": {"selected_word": "coffee"}},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["unit_completed"] is True
    assert body["reward"]["reward"]["xp_earned"] == 75
    assert body["reward"]["reward"]["coin_earned"] == 6
    assert body["reward"]["dashboard"]["xp"]["total"] == 75
    assert body["reward"]["dashboard"]["coin"]["balance"] == 6

    retry = await test_client.post(
        f"/api/lessons/{lesson.id}/attempt",
        json={"answer": {"selected_word": "coffee"}},
    )
    assert retry.status_code == 201
    assert retry.json()["reward"] is None
    user = await db_session.get(User, test_user.id)
    assert user.total_xp == 75
    assert user.coin_balance == 6


@pytest.mark.asyncio
async def test_level_curve_and_level_coin_rewards(test_client, admin_client, db_session, test_user):
    _, lesson = await _seed_reward_lesson(db_session, xp_reward=250, coin_reward=0)
    settings = await admin_client.put(
        "/api/admin/gamification/settings",
        json={"level_coin_rewards": {"2": 10, "3": 20}, "reason": "level rewards"},
    )
    assert settings.status_code == 200

    response = await test_client.post(
        f"/api/lessons/{lesson.id}/attempt",
        json={"answer": {"selected_word": "coffee"}},
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
async def test_shop_redeem_physical_product_requires_and_spends_coin(test_client, db_session, test_user):
    product = ShopProduct(
        code="cap",
        name="Mũ AI Talk",
        description="Mũ lưu niệm",
        price_coin=500,
        stock_quantity=2,
        is_active=True,
        sort_order=1,
    )
    db_session.add(product)
    await db_session.commit()

    shop = await test_client.get("/api/gamification/shop")
    assert shop.status_code == 200
    assert [item["code"] for item in shop.json()["items"]] == ["cap"]

    payload = {
        "product_code": "cap",
        "recipient_name": "Nguyen Van A",
        "phone": "0900000000",
        "address": "1 Nguyen Trai, Ha Noi",
        "note": "Call before delivery",
    }
    poor = await test_client.post("/api/gamification/shop/redeem", json=payload)
    assert poor.status_code == 400

    user = await db_session.get(User, test_user.id)
    user.coin_balance = 500
    await db_session.commit()

    purchase = await test_client.post("/api/gamification/shop/redeem", json=payload)

    assert purchase.status_code == 200
    body = purchase.json()
    assert body["coin_spent"] == 500
    assert body["dashboard"]["coin"]["balance"] == 0
    assert body["redemption"]["status"] == "pending"
    refreshed = await db_session.get(User, test_user.id)
    assert refreshed.subscription.tier != "PRO"
    refreshed_product = await db_session.get(ShopProduct, product.id)
    assert refreshed_product.stock_quantity == 1
    redemptions = (await db_session.execute(ShopRedemption.__table__.select())).all()
    assert len(redemptions) == 1


@pytest.mark.asyncio
async def test_shop_hides_inactive_and_out_of_stock_products(test_client, db_session):
    db_session.add_all([
        ShopProduct(code="active", name="Active", description="Shown", price_coin=1, stock_quantity=1, is_active=True),
        ShopProduct(code="hidden", name="Hidden", description="Hidden", price_coin=1, stock_quantity=1, is_active=False),
        ShopProduct(code="sold", name="Sold", description="Sold", price_coin=1, stock_quantity=0, is_active=True),
    ])
    await db_session.commit()

    response = await test_client.get("/api/gamification/shop")

    assert response.status_code == 200
    assert [item["code"] for item in response.json()["items"]] == ["active"]


@pytest.mark.asyncio
async def test_shop_redemptions_returns_only_current_user_orders_sorted(test_client, db_session, test_user):
    other_user = User(
        email="other-shop@example.com",
        password_hash=hash_password("password123"),
        display_name="Other Shop User",
        level="A1",
        preferences={"is_admin": False},
    )
    product = ShopProduct(
        code="notebook",
        name="Notebook",
        description="Notebook",
        price_coin=100,
        stock_quantity=10,
        is_active=True,
    )
    db_session.add_all([other_user, product])
    await db_session.flush()
    older = ShopRedemption(
        user_id=test_user.id,
        product_id=product.id,
        product_name="Old Notebook",
        price_coin=100,
        recipient_name="Nguyen Van A",
        phone="0900000000",
        address="Old address",
        note="Old note",
        status="pending",
    )
    newer = ShopRedemption(
        user_id=test_user.id,
        product_id=product.id,
        product_name="New Notebook",
        price_coin=120,
        recipient_name="Nguyen Van A",
        phone="0900000001",
        address="New address",
        note=None,
        status="shipping",
    )
    other = ShopRedemption(
        user_id=other_user.id,
        product_id=product.id,
        product_name="Other Notebook",
        price_coin=100,
        recipient_name="Other User",
        phone="0900000002",
        address="Other address",
        status="completed",
    )
    db_session.add_all([older, newer, other])
    await db_session.flush()
    newer.created_at = older.created_at + timedelta(minutes=5)
    await db_session.commit()

    response = await test_client.get("/api/gamification/shop/redemptions")

    assert response.status_code == 200
    body = response.json()
    assert [item["product_name"] for item in body] == ["New Notebook", "Old Notebook"]
    assert body[0]["status"] == "shipping"
    assert body[0]["price_coin"] == 120
    assert all(item["product_name"] != "Other Notebook" for item in body)


@pytest.mark.asyncio
async def test_shop_redemptions_requires_auth(client):
    response = await client.get("/api/gamification/shop/redemptions")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_speaking_session_start_does_not_require_gamification_currency(test_client, test_scenario):
    response = await test_client.post(
        "/api/sessions",
        json={"scenario_id": test_scenario.id},
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_leaderboard_returns_current_week_xp_by_default(test_client, db_session, test_user):
    today = datetime.now(timezone.utc).date()
    previous_week = today - timedelta(days=today.weekday() + 1)

    competitor = User(
        email="leader@example.com",
        password_hash=hash_password("leader123"),
        display_name="Leaderboard Pro",
        level="C1",
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
            DailyStat(user_id=test_user.id, date=previous_week, xp_earned=900),
            DailyStat(user_id=competitor.id, date=today, xp_earned=280),
            DailyStat(user_id=competitor.id, date=previous_week, xp_earned=10),
        ]
    )
    await db_session.commit()

    weekly_response = await test_client.get("/api/gamification/leaderboard?limit=5")

    assert weekly_response.status_code == 200
    weekly_body = weekly_response.json()
    assert weekly_body["period"] == "weekly"
    assert weekly_body["available_periods"] == ["weekly"]
    assert weekly_body["entries"][0]["display_name"] == "Leaderboard Pro"
    assert weekly_body["entries"][0]["score"] == 280
    assert weekly_body["current_user"]["display_name"] == "Test User"
    assert weekly_body["current_user"]["score"] == 120
    assert weekly_body["current_user"]["rank"] == 2

    all_time_response = await test_client.get("/api/gamification/leaderboard?period=all_time&limit=5")

    assert all_time_response.status_code == 422
