import pytest
from app.models.user import User

@pytest.mark.asyncio
async def test_login_success(client, test_user):
    """Test successful login with correct credentials."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_password(client, test_user):
    """Test login failure with incorrect password."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_login_non_existent_user(client):
    """Test login failure with non-existent email."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_login_validation_error(client):
    """Test login validation errors for missing fields."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "not-an-email"}
    )
    # FastAPI returns 422 Unprocessable Entity for Pydantic validation errors
    assert response.status_code == 422

# ─── Registration Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client):
    """Test successful user registration."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user):
    """Test registration failure with an existing email."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_register_validation_error(client):
    """Test registration validation errors."""
    response = await client.post(
        "/api/auth/register",
        json={"email": "invalid-email"}
    )
    assert response.status_code == 422

# ─── User Profile Tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_success(client, test_user):
    """Test retrieving current user information."""
    # Login first to get token
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"

@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    """Test retrieving user info without authentication."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401

# ─── Onboarding Tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_onboard_success(client, db_session):
    """Test completing user onboarding."""
    # Create user manually
    from app.core.security import hash_password
    user = User(
        email="onboard@example.com",
        password_hash=hash_password("password123"),
        is_onboarding_completed=False
    )
    db_session.add(user)
    await db_session.commit()
    
    # Login to get token
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "onboard@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    
    onboard_data = {
        "display_name": "Updated Name",
        "native_language": "vi",
        "avatar": "avatar_1",
        "age": 25,
        "level": "intermediate",
        "learning_purpose": "career",
        "main_challenge": "speaking",
        "favorite_topics": "tech, travel",
        "daily_goal": 30
    }
    
    response = await client.put(
        "/api/auth/me/onboard",
        json=onboard_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"
    assert data["is_onboarding_completed"] is True

@pytest.mark.asyncio
async def test_onboard_already_completed(client, test_user, db_session):
    """Test that onboarding cannot be completed twice."""
    # Set user as already onboarded
    test_user.is_onboarding_completed = True
    await db_session.flush()
    
    # Login to get token
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    
    onboard_data = {
        "display_name": "Another Update",
        "native_language": "en",
        "avatar": "avatar_2",
        "age": 35,
        "level": "advanced",
        "learning_purpose": "travel",
        "main_challenge": "vocabulary",
        "favorite_topics": "food",
        "daily_goal": 60
    }
    
    response = await client.put(
        "/api/auth/me/onboard",
        json=onboard_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Onboarding already completed"
