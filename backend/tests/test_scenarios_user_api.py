import pytest


@pytest.mark.asyncio
async def test_user_scenarios_list_includes_active_sqlite_legacy_rows(client, test_scenario):
    response = await client.get("/api/scenarios")

    assert response.status_code == 200, response.text
    items = response.json()
    assert any(item["id"] == test_scenario.id for item in items)
    assert any(item["id"] == test_scenario.id and item["is_pro"] is False for item in items)


@pytest.mark.asyncio
async def test_free_user_cannot_get_pro_scenario_detail(client, db_session, test_user, test_scenario):
    from app.core.security import create_access_token

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
    from app.core.security import create_access_token

    test_scenario.is_pro = True
    await db_session.commit()

    token = create_access_token(test_admin_user.id)
    response = await client.get(
        f"/api/scenarios/{test_scenario.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_pro"] is True
