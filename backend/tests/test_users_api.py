import pytest

from app.core.security import create_access_token, hash_password, verify_password


@pytest.mark.asyncio
async def test_patch_me_updates_partial_profile_without_completing_onboarding(client, test_user):
    token = create_access_token(user_id=test_user.id)

    response = await client.patch(
        "/api/users/me",
        json={
            "display_name": "Profile Owner",
            "favorite_topics": ["travel", "business"],
            "preferences": {"voice_feedback": False, "is_admin": False},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Profile Owner"
    assert data["favorite_topics"] == ["travel", "business"]
    assert data["preferences"]["voice_feedback"] is False
    assert data["is_onboarding_completed"] is False


@pytest.mark.asyncio
async def test_patch_me_rejects_empty_payload(client, test_user):
    token = create_access_token(user_id=test_user.id)

    response = await client.patch(
        "/api/users/me",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_password_updates_password_hash(client, db_session, test_user):
    token = create_access_token(user_id=test_user.id)

    response = await client.post(
        "/api/users/me/change-password",
        json={
            "current_password": "password123",
            "new_password": "Newpass456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    await db_session.refresh(test_user)

    assert response.status_code == 200
    assert response.json()["detail"] == "Password updated successfully."
    assert verify_password("Newpass456", test_user.password_hash)


@pytest.mark.asyncio
async def test_change_password_rejects_invalid_current_password(client, test_user):
    token = create_access_token(user_id=test_user.id)

    response = await client.post(
        "/api/users/me/change-password",
        json={
            "current_password": "wrong-password",
            "new_password": "Newpass456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect."


@pytest.mark.asyncio
async def test_change_password_rejects_google_user_without_password(
    client, db_session, test_google_user
):
    token = create_access_token(user_id=test_google_user.id)

    response = await client.post(
        "/api/users/me/change-password",
        json={
            "current_password": "",
            "new_password": "Newpass456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    await db_session.refresh(test_google_user)

    assert response.status_code == 400
    assert response.json()["detail"] == "Please use forgot password OTP flow to set a password."
    assert test_google_user.password_hash is None


@pytest.mark.asyncio
async def test_change_password_requires_current_password_when_password_already_exists(
    client, test_google_user, db_session
):
    test_google_user.password_hash = hash_password("Existing123")
    await db_session.commit()
    await db_session.refresh(test_google_user)
    token = create_access_token(user_id=test_google_user.id)

    response = await client.post(
        "/api/users/me/change-password",
        json={
            "new_password": "Newpass456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is required."
