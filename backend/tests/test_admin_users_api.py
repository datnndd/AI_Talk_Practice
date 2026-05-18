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
async def test_admin_users_list_paginates_in_database(admin_client, db_session):
    db_session.add_all(
        [
            User(
                email=f"page-user-{index:02d}@example.com",
                display_name=f"Page User {index:02d}",
                preferences={"is_admin": False},
            )
            for index in range(15)
        ]
    )
    await db_session.commit()

    response = await admin_client.get(
        "/api/admin/users",
        params={"search": "page-user-", "status": "active", "page": 2, "page_size": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert data["page"] == 2
    assert data["page_size"] == 5
    assert len(data["items"]) == 5

@pytest.mark.asyncio
async def test_admin_users_list_filters_admin_role_from_preferences(admin_client, db_session):
    db_session.add_all(
        [
            User(
                email="role-admin-pref@example.com",
                display_name="Role Admin Pref",
                role="user",
                preferences={"is_admin": True},
            ),
            User(
                email="role-learner-pref@example.com",
                display_name="Role Learner Pref",
                role="user",
                preferences={"is_admin": False},
            ),
        ]
    )
    await db_session.commit()

    admin_response = await admin_client.get(
        "/api/admin/users",
        params={"search": "role-", "role": "admin", "status": "active"},
    )
    learner_response = await admin_client.get(
        "/api/admin/users",
        params={"search": "role-", "role": "learner", "status": "active"},
    )

    assert admin_response.status_code == 200
    assert learner_response.status_code == 200
    assert [item["email"] for item in admin_response.json()["items"]] == ["role-admin-pref@example.com"]
    assert [item["email"] for item in learner_response.json()["items"]] == ["role-learner-pref@example.com"]

@pytest.mark.asyncio
async def test_admin_can_get_and_update_user(admin_client, test_user):
    response = await admin_client.put(
        f"/api/admin/users/{test_user.id}",
        json={
            "display_name": "Updated Learner",
            "level": "B2",
            "favorite_topics": ["travel", "networking"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Learner"
    assert data["level"] == "B2"
    assert data["favorite_topics"] == ["travel", "networking"]


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

    update_response = await admin_client.put(
        f"/api/admin/users/{test_admin_user.id}",
        json={"is_admin": False},
    )
    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "You cannot change your own admin access."

    deactivate_response = await admin_client.post(f"/api/admin/users/{test_admin_user.id}/deactivate")
    assert deactivate_response.status_code == 400
    assert deactivate_response.json()["detail"] == "You cannot deactivate your own account."
