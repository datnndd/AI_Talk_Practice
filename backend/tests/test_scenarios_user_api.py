import pytest


@pytest.mark.asyncio
async def test_user_scenarios_list_includes_active_sqlite_legacy_rows(client, test_scenario):
    response = await client.get("/api/scenarios")

    assert response.status_code == 200, response.text
    items = response.json()
    assert any(item["id"] == test_scenario.id for item in items)
