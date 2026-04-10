import pytest

from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User


@pytest.mark.asyncio
async def test_admin_users_list_requires_admin(test_client):
    response = await test_client.get("/api/admin/users")

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access is required"


@pytest.mark.asyncio
async def test_admin_can_list_and_filter_users(admin_client, db_session, test_user):
    archived_user = User(
        email="archived@example.com",
        display_name="Archived Learner",
        native_language="vi",
        target_language="en",
        level="A2",
        preferences={"is_admin": False},
    )
    db_session.add(archived_user)
    await db_session.flush()
    db_session.add(
        Subscription(
            user_id=archived_user.id,
            tier="PRO",
            status="active",
        )
    )
    archived_user.deleted_at = test_user.created_at
    await db_session.commit()

    response = await admin_client.get(
        "/api/admin/users",
        params={"search": "test@", "role": "learner", "status": "active"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["email"] == "test@example.com"
    assert data["items"][0]["is_admin"] is False


@pytest.mark.asyncio
async def test_admin_can_get_and_update_user(admin_client, test_user):
    response = await admin_client.put(
        f"/api/admin/users/{test_user.id}",
        json={
            "display_name": "Updated Learner",
            "level": "B2",
            "favorite_topics": ["travel", "networking"],
            "daily_goal": 25,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Learner"
    assert data["level"] == "B2"
    assert data["favorite_topics"] == ["travel", "networking"]
    assert data["daily_goal"] == 25


@pytest.mark.asyncio
async def test_admin_can_toggle_admin_access(admin_client, test_user):
    promote_response = await admin_client.post(f"/api/admin/users/{test_user.id}/toggle-admin")
    assert promote_response.status_code == 200
    assert promote_response.json()["is_admin"] is True

    demote_response = await admin_client.post(f"/api/admin/users/{test_user.id}/toggle-admin")
    assert demote_response.status_code == 200
    assert demote_response.json()["is_admin"] is False


@pytest.mark.asyncio
async def test_admin_can_update_user_subscription_plan(admin_client, test_user):
    response = await admin_client.put(
        f"/api/admin/users/{test_user.id}/subscription",
        json={"tier": "PRO"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["subscription"]["tier"] == "PRO"
    assert data["subscription"]["status"] == "active"
    assert data["subscription"]["expires_at"] is not None


@pytest.mark.asyncio
async def test_admin_can_deactivate_and_restore_user(admin_client, test_user):
    deactivate_response = await admin_client.post(f"/api/admin/users/{test_user.id}/deactivate")
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["deleted_at"] is not None

    list_response = await admin_client.get("/api/admin/users", params={"status": "active"})
    active_user_ids = [item["id"] for item in list_response.json()["items"]]
    assert test_user.id not in active_user_ids

    restore_response = await admin_client.post(f"/api/admin/users/{test_user.id}/restore")
    assert restore_response.status_code == 200
    assert restore_response.json()["deleted_at"] is None


@pytest.mark.asyncio
async def test_admin_cannot_change_own_admin_access_or_deactivate_self(admin_client, test_admin_user):
    toggle_response = await admin_client.post(f"/api/admin/users/{test_admin_user.id}/toggle-admin")
    assert toggle_response.status_code == 400
    assert toggle_response.json()["detail"] == "You cannot change your own admin access."

    deactivate_response = await admin_client.post(f"/api/admin/users/{test_admin_user.id}/deactivate")
    assert deactivate_response.status_code == 400
    assert deactivate_response.json()["detail"] == "You cannot deactivate your own account."
