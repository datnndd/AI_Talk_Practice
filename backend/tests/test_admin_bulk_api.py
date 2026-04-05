import pytest
import pytest_asyncio
from app.modules.scenarios.models.scenario import Scenario

@pytest_asyncio.fixture
async def multiple_scenarios(db_session):
    """Seed multiple scenarios for bulk action testing."""
    scenarios = []
    for i in range(3):
        scenario = Scenario(
            title=f"Scenario {i}",
            description=f"Description {i}",
            ai_system_prompt="You are a helper. Role: Assistant. Coaching: Yes. Tone: Character. Avoid: Drift. Tone: Persona. Correct: Feedback. Negative: No.",
            category="travel",
            difficulty="medium",
            is_active=False
        )
        db_session.add(scenario)
        scenarios.append(scenario)
    await db_session.flush()
    for s in scenarios:
        await db_session.refresh(s)
    return scenarios

@pytest.mark.asyncio
async def test_bulk_activate_scenarios(admin_client, multiple_scenarios, db_session):
    """Test bulk activating scenarios."""
    scenario_ids = [s.id for s in multiple_scenarios]
    
    response = await admin_client.post(
        "/api/admin/scenarios/bulk-actions",
        json={
            "scenario_ids": scenario_ids,
            "action": "activate"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Bulk action applied"
    
    # Reload and verify
    for sid in scenario_ids:
        # We need a new session or refresh to see changes if they were committed in another session
        # But here the app uses the same db_session override, so we can just re-query
        from sqlalchemy import select
        res = await db_session.execute(select(Scenario).where(Scenario.id == sid))
        scenario = res.scalar_one()
        assert scenario.is_active is True

@pytest.mark.asyncio
async def test_bulk_deactivate_scenarios(admin_client, multiple_scenarios, db_session):
    """Test bulk deactivating scenarios."""
    # First activate them
    for s in multiple_scenarios:
        s.is_active = True
    await db_session.commit()
    
    scenario_ids = [s.id for s in multiple_scenarios]
    
    response = await admin_client.post(
        "/api/admin/scenarios/bulk-actions",
        json={
            "scenario_ids": scenario_ids,
            "action": "deactivate"
        }
    )
    
    assert response.status_code == 200
    
    for sid in scenario_ids:
        from sqlalchemy import select
        res = await db_session.execute(select(Scenario).where(Scenario.id == sid))
        scenario = res.scalar_one()
        assert scenario.is_active is False

@pytest.mark.asyncio
async def test_bulk_soft_delete_scenarios(admin_client, multiple_scenarios, db_session):
    """Test bulk soft deleting scenarios."""
    scenario_ids = [s.id for s in multiple_scenarios]
    
    response = await admin_client.post(
        "/api/admin/scenarios/bulk-actions",
        json={
            "scenario_ids": scenario_ids,
            "action": "soft_delete"
        }
    )
    
    assert response.status_code == 200
    
    for sid in scenario_ids:
        from sqlalchemy import select
        res = await db_session.execute(select(Scenario).where(Scenario.id == sid))
        scenario = res.scalar_one()
        assert scenario.deleted_at is not None
        assert scenario.is_active is False

@pytest.mark.asyncio
async def test_bulk_generate_variations_task_lifecycle(admin_client, multiple_scenarios):
    """Test bulk generating variations and tracking the task."""
    scenario_ids = [s.id for s in multiple_scenarios]
    
    # Trigger generation
    response = await admin_client.post(
        "/api/admin/scenarios/bulk-actions",
        json={
            "scenario_ids": scenario_ids,
            "action": "generate_variations",
            "generation_count": 2
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Background generation started"
    assert "task" in data
    task_id = data["task"]["task_id"]
    assert task_id is not None
    
    # Check task status
    response = await admin_client.get(f"/api/admin/generation-tasks/{task_id}")
    assert response.status_code == 200
    task_data = response.json()
    assert task_data["task_id"] == task_id
    assert task_data["status"] in ["queued", "running", "completed", "failed"]

@pytest.mark.asyncio
async def test_bulk_action_unauthorized(test_client, multiple_scenarios):
    """Test bulk action fails for non-admin."""
    scenario_ids = [s.id for s in multiple_scenarios]
    
    response = await test_client.post(
        "/api/admin/scenarios/bulk-actions",
        json={
            "scenario_ids": scenario_ids,
            "action": "activate"
        }
    )
    
    assert response.status_code == 403
