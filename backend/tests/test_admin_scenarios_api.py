import pytest

from app.core.security import create_access_token, hash_password
from app.modules.users.models.user import User


async def _create_admin_user(db_session):
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("password123"),
        display_name="Admin",
        native_language="en",
        target_language="en",
        level="advanced",
        preferences={"is_admin": True},
    )
    db_session.add(admin)
    await db_session.flush()
    await db_session.refresh(admin)
    return admin


@pytest.mark.asyncio
async def test_admin_route_requires_admin(client, test_user):
    token = create_access_token(test_user.id)
    response = await client.get(
        "/api/admin/scenarios",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Admin access is required"


@pytest.mark.asyncio
async def test_admin_can_create_scenario_and_prompt_history(client, db_session):
    admin = await _create_admin_user(db_session)
    token = create_access_token(admin.id)

    payload = {
        "title": "Hotel Check-in Escalation",
        "description": "Learner handles a late-night hotel check-in where the reservation is missing and must stay calm while clarifying the problem.",
        "category": "travel",
        "difficulty": "medium",
        "ai_system_prompt": (
            "You are a calm hotel receptionist. Stay in character, ask follow-up questions, "
            "coach the learner with brief corrections, and keep the conversation focused on "
            "solving the missing reservation issue without breaking roleplay."
        ),
        "learning_objectives": ["clarify a booking issue", "ask for confirmation details"],
        "target_skills": ["fluency", "grammar"],
        "tags": ["hotel", "travel", "problem-solving"],
        "estimated_duration_minutes": 12,
        "is_pre_generated": True,
        "pre_gen_count": 10,
        "mode": "roleplay",
        "metadata": {"persona": "front desk"},
    }

    response = await client.post(
        "/api/admin/scenarios",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == payload["title"]
    assert body["estimated_duration_minutes"] == 12
    assert body["variation_count"] == 0
    assert len(body["prompt_history"]) == 1
    assert body["prompt_history"][0]["quality_score"] >= 70


@pytest.mark.asyncio
async def test_admin_can_create_and_list_variations(client, db_session, test_scenario):
    admin = await _create_admin_user(db_session)
    token = create_access_token(admin.id)

    payload = {
        "scenario_id": test_scenario.id,
        "variation_name": "Formal airport queue",
        "parameters": {"tone": "formal", "stress_level": "high"},
        "sample_prompt": "The airport line is long and the learner needs concise, polite responses.",
        "sample_conversation": [
            {"role": "assistant", "content": "Good evening. Passport and ticket, please."},
            {"role": "user", "content": "Of course. I also need help finding my gate."},
        ],
        "is_active": True,
        "is_pregenerated": True,
        "is_approved": True,
    }

    create_response = await client.post(
        "/api/admin/scenario-variations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["variation_name"] == payload["variation_name"]
    assert created["is_pregenerated"] is True

    list_response = await client.get(
        f"/api/admin/scenario-variations?scenario_id={test_scenario.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert any(item["variation_name"] == payload["variation_name"] for item in items)
