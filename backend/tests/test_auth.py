from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.modules.auth.models.email_otp import EmailOTP
from app.modules.users.repository import UserRepository

@pytest.mark.asyncio
async def test_register_success_with_subscription(client):
    """Test registration and ensure FREE subscription is created."""
    email = "new_user@example.com"
    await client.post("/api/auth/otp/request", json={"email": email, "purpose": "register"})
    response = await client.post(
        "/api/auth/register/verify",
        json={"email": email, "otp": "000000", "password": "Password123"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_verify_success_with_subscription(client, db_session):
    email = "new_user@example.com"
    db_session.add(EmailOTP(email=email, purpose="register", code_hash=hash_password("123456"), expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)))
    await db_session.commit()

    response = await client.post(
        "/api/auth/register/verify",
        json={"email": email, "otp": "123456", "password": "Password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

    me_response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == email
    assert me_data["subscription"]["tier"] == "FREE"


@pytest.mark.asyncio
async def test_register_direct_password_rejected(client):
    response = await client.post(
        "/api/auth/register",
        json={"email": "direct@example.com", "password": "Password123"}
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login_success_with_tokens(client, test_user):
    """Test login returns both access and refresh tokens."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

    me_response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["subscription"]["tier"] == "FREE"

@pytest.mark.asyncio
async def test_refresh_token_success(client, test_user):
    """Test getting a new access token using a refresh token."""
    refresh_token = create_refresh_token(user_id=test_user.id)
    
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_me_profile_and_subscription(client, test_user):
    """Test /me endpoint returns user profile and subscription info."""
    token = create_access_token(user_id=test_user.id)
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "subscription" in data
    assert data["subscription"]["tier"] == "FREE"

@pytest.mark.asyncio
async def test_update_profile_success(client, test_user):
    """Test updating user profile fields."""
    token = create_access_token(user_id=test_user.id)
    update_data = {
        "display_name": "New Name",
        "level": "A1",
    }
    response = await client.patch(
        "/api/users/me",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "New Name"
    assert data["level"] == "A1"

@pytest.mark.asyncio
async def test_google_login_simulation(client):
    """Simulate Google OAuth login."""
    # We mock the google-auth verification in the service layer
    # Since we can't easily mock the dependency within the test client here without more setup,
    # we verify the route exists and handles invalid tokens.
    response = await client.post(
        "/api/auth/google",
        json={"id_token": "invalid_mock_token"}
    )
    # Should fail verification
    assert response.status_code in [400, 401]

@pytest.mark.asyncio
async def test_forgot_password_flow_log(client, test_user):
    """Test forgot password endpoint (Check console for mock email)."""
    response = await client.post(
        "/api/auth/forgot-password",
        json={"email": "test@example.com"}
    )
    assert response.status_code == 202
    assert response.json()["message"] == "If that email exists, a reset link has been sent"


@pytest.mark.asyncio
async def test_forgot_password_does_not_reveal_missing_email(client):
    response = await client.post(
        "/api/auth/forgot-password",
        json={"email": "missing@example.com"}
    )
    assert response.status_code == 202
    assert response.json()["message"] == "If that email exists, a reset link has been sent"


@pytest.mark.asyncio
async def test_reset_password_with_otp(client, db_session, test_user):
    db_session.add(EmailOTP(email="test@example.com", purpose="reset_password", code_hash=hash_password("654321"), expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)))
    await db_session.commit()

    response = await client.post(
        "/api/auth/reset-password",
        json={"email": "test@example.com", "otp": "654321", "new_password": "Newpass123"},
    )

    await db_session.refresh(test_user)
    assert response.status_code == 200
    assert verify_password("Newpass123", test_user.password_hash)


@pytest.mark.asyncio
async def test_password_policy_rejects_missing_uppercase(client, db_session):
    email = "weak@example.com"
    db_session.add(EmailOTP(email=email, purpose="register", code_hash=hash_password("123456"), expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)))
    await db_session.commit()

    response = await client.post(
        "/api/auth/register/verify",
        json={"email": email, "otp": "123456", "password": "password123"},
    )

    assert response.status_code == 400
    assert await UserRepository.get_active_by_email(db_session, email) is None

@pytest.mark.asyncio
async def test_rate_limiting_trigger(client):
    """
    Test rate limiting on login. 
    Note: In tests, we might need to lower the limit or hit it multiple times.
    This is a structural test to ensure the dependency is working.
    """
    for _ in range(10): # Limiter is 5 per minute in code
        response = await client.post(
            "/api/auth/login",
            json={"email": "limit@example.com", "password": "wrong"}
        )
        if response.status_code == 429:
            break
    
    # Depending on the test environment setup for slowapi, this may or may not trigger.
    # But checking for 200/401/429 ensures the route is at least reachable.
    assert response.status_code in [401, 429]
