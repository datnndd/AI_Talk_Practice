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
async def test_admin_can_create_scenario(client, db_session):
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
        "tasks": ["Say your name", "Explain the missing reservation", "Ask for the next step"],
        "tags": ["hotel", "travel", "problem-solving"],
        "estimated_duration_minutes": 12,
    }

    response = await client.post(
        "/api/admin/scenarios",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == payload["title"]
    assert body["tasks"] == payload["tasks"]
    assert body["estimated_duration_minutes"] == 12
    assert "variation_count" not in body
    assert "active_variation_count" not in body
    assert "variations" not in body
    assert "prompt_history" not in body


@pytest.mark.asyncio
async def test_admin_can_generate_default_prompt_and_create_scenario_with_roles(client, db_session):
    admin = await _create_admin_user(db_session)
    token = create_access_token(admin.id)

    prompt_request = {
        "title": "Coffee Shop Delay",
        "description": "Learner is at a busy coffee shop where an order is delayed and must politely ask for an update without sounding impatient.",
        "ai_role": "Busy but friendly barista",
        "user_role": "Customer waiting for a coffee order",
        "tasks": ["Ask for an order update", "Respond politely to a delay"],
    }

    prompt_response = await client.post(
        "/api/admin/scenarios/generate-default-prompt",
        headers={"Authorization": f"Bearer {token}"},
        json=prompt_request,
    )

    assert prompt_response.status_code == 200, prompt_response.text
    generated_prompt = prompt_response.json()["prompt"]
    assert "Coffee Shop Delay" in generated_prompt
    assert "Busy but friendly barista" in generated_prompt
    assert "Customer waiting for a coffee order" in generated_prompt
    assert "Ask for an order update" in generated_prompt

    payload = {
        **prompt_request,
        "category": "travel",
        "difficulty": "easy",
        "ai_system_prompt": generated_prompt,
        "tags": ["coffee", "polite"],
    }

    response = await client.post(
        "/api/admin/scenarios",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["ai_role"] == "Busy but friendly barista"
    assert body["user_role"] == "Customer waiting for a coffee order"
    assert "Coffee Shop Delay" in body["ai_system_prompt"]
    assert "Busy but friendly barista" in body["ai_system_prompt"]


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


@pytest.mark.asyncio
async def test_admin_scenario_detail_endpoint_is_removed(client, db_session, test_scenario):
    admin = await _create_admin_user(db_session)
    token = create_access_token(admin.id)

    response = await client.get(
        f"/api/admin/scenarios/{test_scenario.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 405


@pytest.mark.asyncio
async def test_admin_can_toggle_scenario_active(client, db_session, test_scenario):
    admin = await _create_admin_user(db_session)
    token = create_access_token(admin.id)

    response = await client.post(
        f"/api/admin/scenarios/{test_scenario.id}/toggle-active",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == test_scenario.id
    assert body["is_active"] is False
    assert body["updated_at"]
