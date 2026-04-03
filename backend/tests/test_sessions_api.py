import pytest
from httpx import AsyncClient
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_api_start_session_pregenerated(client, test_user, test_scenario, test_variation):
    """Test starting a session using a pre-generated variation."""
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "scenario_id": test_scenario.id,
        "prefer_pregenerated": True
    }
    response = await client.post("/api/sessions", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["scenario_id"] == test_scenario.id
    assert data["variation_id"] == test_variation.id
    assert data["status"] == "active"
    assert "variation_seed" in data["metadata"]

@pytest.mark.asyncio
async def test_api_start_session_realtime_variation(client, test_user, test_scenario):
    """Test starting a session that triggers real-time variation creation."""
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "scenario_id": test_scenario.id,
        "variation_parameters": {"topic": "delay"},
        "create_variation_if_missing": True,
        "mode": "debate"
    }
    response = await client.post("/api/sessions", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["scenario_id"] == test_scenario.id
    assert data["variation_id"] is not None
    assert data["mode"] == "debate"

@pytest.mark.asyncio
async def test_api_session_lifecycle(client, test_user, test_session):
    """Test adding a message and completing a session via API."""
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Add Message
    msg_payload = {
        "role": "user",
        "content": "Hello, I have a reservation.",
        "score": {
            "pronunciation_score": 8.0,
            "fluency_score": 8.0,
            "grammar_score": 8.0,
            "vocabulary_score": 8.0,
            "intonation_score": 8.0,
            "overall_score": 8.0
        }
    }
    response = await client.post(f"/api/sessions/{test_session.id}/messages", json=msg_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hello, I have a reservation."
    assert data["score"] is not None
    assert data["score"]["overall_score"] == 8.0
    
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
    assert data["score"] is not None
    assert data["score"]["overall_score"] == 8.0

@pytest.mark.asyncio
async def test_api_get_session_not_found(client, test_user):
    """Test error when session is not found."""
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/sessions/99999", headers=headers)
    assert response.status_code == 404
