import pytest
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_api_start_session_ignores_legacy_variation_payload(client, test_user, test_scenario):
    """Starting a session no longer resolves or stores scenario variations."""
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "scenario_id": test_scenario.id,
        "variation_id": 9999,
        "variation_seed": "legacy-seed",
        "variation_parameters": {"topic": "delay"},
        "prefer_pregenerated": True,
        "create_variation_if_missing": True,
        "mode": "debate",
    }
    response = await client.post("/api/sessions", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["scenario_id"] == test_scenario.id
    assert data["status"] == "active"
    assert data["mode"] == "debate"
    assert "variation_id" not in data
    assert "variation_seed" not in data
    assert "variation" not in data
    assert "variation_seed" not in data["metadata"]

@pytest.mark.asyncio
async def test_api_session_lifecycle(client, test_user, test_session):
    """Test adding a message and completing a session via API."""
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Add Message
    msg_payload = {
        "role": "user",
        "content": "Hello, I have a reservation.",
    }
    response = await client.post(f"/api/sessions/{test_session.id}/messages", json=msg_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hello, I have a reservation."
    assert "score" not in data
    
    # 2. Get Session (verify message is there)
    response = await client.get(f"/api/sessions/{test_session.id}", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["messages"]) == 1
    
    # 3. End Session
    end_payload = {
        "status": "completed",
        "feedback_summary": "Session ended successfully."
    }
    response = await client.post(f"/api/sessions/{test_session.id}/end", json=end_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["score"] is None

@pytest.mark.asyncio
async def test_api_get_session_not_found(client, test_user):
    """Test error when session is not found."""
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/sessions/99999", headers=headers)
    assert response.status_code == 404
