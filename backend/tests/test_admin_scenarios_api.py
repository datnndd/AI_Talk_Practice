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
    assert response.status_code == 403
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
    assert body["learning_objectives"] == payload["learning_objectives"]
    assert body["estimated_duration_minutes"] == 12
    assert "variation_count" not in body
    assert "active_variation_count" not in body
    assert "variations" not in body
    assert len(body["prompt_history"]) == 1
    assert body["prompt_history"][0]["quality_score"] >= 70


@pytest.mark.asyncio
async def test_admin_variation_endpoints_are_removed(client, db_session, test_scenario):
    admin = await _create_admin_user(db_session)
    token = create_access_token(admin.id)

    create_response = await client.post(
        "/api/admin/scenario-variations",
        headers={"Authorization": f"Bearer {token}"},
        json={"scenario_id": test_scenario.id, "variation_name": "Legacy"},
    )
    assert create_response.status_code == 404

    list_response = await client.get(
        f"/api/admin/scenario-variations?scenario_id={test_scenario.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 404
