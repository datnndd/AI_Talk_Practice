import pytest

from app.core.security import create_access_token
from app.modules.sessions.models.session import Session
from app.modules.sessions.models.session_score import SessionScore


@pytest.mark.asyncio
async def test_user_scenarios_list_includes_active_sqlite_legacy_rows(client, test_scenario):
    response = await client.get("/api/scenarios")

    assert response.status_code == 200, response.text
    items = response.json()
    assert any(item["id"] == test_scenario.id for item in items)
    assert any(item["id"] == test_scenario.id and item["is_pro"] is False for item in items)
    scenario_item = next(item for item in items if item["id"] == test_scenario.id)
    assert "title" in scenario_item
    assert "description" in scenario_item
    assert "category" in scenario_item
    assert "difficulty" in scenario_item
    assert "ai_system_prompt" not in scenario_item
    assert "has_completed_session" in scenario_item
    assert "latest_completed_session_result_url" in scenario_item


@pytest.mark.asyncio
async def test_free_user_cannot_get_pro_scenario_detail(client, db_session, test_user, test_scenario):
    test_scenario.is_pro = True
    await db_session.commit()

    token = create_access_token(test_user.id)
    response = await client.get(
        f"/api/scenarios/{test_scenario.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_vip_user_can_get_pro_scenario_detail(client, db_session, test_admin_user, test_scenario):
    test_scenario.is_pro = True
    await db_session.commit()

    token = create_access_token(test_admin_user.id)
    response = await client.get(
        f"/api/scenarios/{test_scenario.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_pro"] is True
    assert "ai_system_prompt" in response.json()

async def _create_scored_session(db_session, *, user_id, scenario_id, objective_completion, status="completed"):
    session = Session(
        user_id=user_id,
        scenario_id=scenario_id,
        status=status,
        session_metadata={},
    )
    db_session.add(session)
    await db_session.flush()
    db_session.add(
        SessionScore(
            session_id=session.id,
            avg_fluency=7.0,
            avg_grammar=7.0,
            avg_vocabulary=7.0,
            relevance_score=7.0,
            overall_score=7.0,
            scored_message_count=1,
            score_metadata={"objective_completion": objective_completion},
        )
    )
    await db_session.commit()
    return session

@pytest.mark.asyncio
async def test_scenario_detail_marks_objective_completed_session(test_client, db_session, test_user, test_scenario):
    session = await _create_scored_session(
        db_session,
        user_id=test_user.id,
        scenario_id=test_scenario.id,
        objective_completion="completed",
    )

    response = await test_client.get(f"/api/scenarios/{test_scenario.id}")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["has_completed_session"] is True
    assert payload["latest_completed_session_id"] == session.id
    assert payload["latest_completed_session_result_url"] == f"/sessions/{session.id}/result"
    assert payload["objective_completion"] == "completed"

@pytest.mark.asyncio
async def test_scenarios_list_marks_objective_completed_session(test_client, db_session, test_user, test_scenario):
    session = await _create_scored_session(
        db_session,
        user_id=test_user.id,
        scenario_id=test_scenario.id,
        objective_completion="completed",
    )

    response = await test_client.get("/api/scenarios")

    assert response.status_code == 200, response.text
    payload = next(item for item in response.json() if item["id"] == test_scenario.id)
    assert payload["has_completed_session"] is True
    assert payload["latest_completed_session_id"] == session.id
    assert payload["latest_completed_session_result_url"] == f"/sessions/{session.id}/result"
    assert payload["objective_completion"] == "completed"

@pytest.mark.asyncio
async def test_scenarios_list_does_not_mark_not_completed_objective(test_client, db_session, test_user, test_scenario):
    await _create_scored_session(
        db_session,
        user_id=test_user.id,
        scenario_id=test_scenario.id,
        objective_completion="not_completed",
    )

    response = await test_client.get("/api/scenarios")

    assert response.status_code == 200, response.text
    payload = next(item for item in response.json() if item["id"] == test_scenario.id)
    assert payload["has_completed_session"] is False
    assert payload["latest_completed_session_id"] is None
    assert payload["latest_completed_session_result_url"] is None
    assert payload["objective_completion"] is None

@pytest.mark.asyncio
async def test_scenario_detail_does_not_mark_not_completed_objective(test_client, db_session, test_user, test_scenario):
    await _create_scored_session(
        db_session,
        user_id=test_user.id,
        scenario_id=test_scenario.id,
        objective_completion="not_completed",
    )

    response = await test_client.get(f"/api/scenarios/{test_scenario.id}")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["has_completed_session"] is False
    assert payload["latest_completed_session_id"] is None
    assert payload["latest_completed_session_result_url"] is None
    assert payload["objective_completion"] is None

@pytest.mark.asyncio
async def test_scenario_detail_does_not_mark_legacy_partial_objective(test_client, db_session, test_user, test_scenario):
    await _create_scored_session(
        db_session,
        user_id=test_user.id,
        scenario_id=test_scenario.id,
        objective_completion="partial",
    )

    response = await test_client.get(f"/api/scenarios/{test_scenario.id}")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["has_completed_session"] is False
    assert payload["latest_completed_session_id"] is None
    assert payload["latest_completed_session_result_url"] is None
    assert payload["objective_completion"] is None

@pytest.mark.asyncio
async def test_scenario_detail_ignores_other_users_objective_completion(
    client,
    db_session,
    test_google_user,
    test_user,
    test_scenario,
):
    await _create_scored_session(
        db_session,
        user_id=test_google_user.id,
        scenario_id=test_scenario.id,
        objective_completion="completed",
    )
    token = create_access_token(test_user.id)

    response = await client.get(
        f"/api/scenarios/{test_scenario.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["has_completed_session"] is False
