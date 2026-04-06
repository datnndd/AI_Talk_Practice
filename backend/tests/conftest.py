import os
import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import JSON

# Monkeypatch JSONB to JSON for SQLite compatibility in tests
postgresql.JSONB = JSON

# Set DATABASE_URL in environment before importing app.main to avoid PostgreSQL connection attempt
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.main import app
from app.db.base_class import Base
from app.db.session import get_db
from app.core.security import hash_password
from app.modules.users.models.user import User
from app.modules.users.models.subscription import Subscription

# Use in-memory SQLite with StaticPool to keep connection open across sessions in tests
engine = create_async_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Create the database tables for the test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Provide a database session for each test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """Provide an AsyncClient for testing the FastAPI app."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client(db_session, test_admin_user):
    """Provide an AsyncClient authenticated as an admin."""
    from app.core.security import create_access_token

    async def override_get_db():
        yield db_session

    token = create_access_token(user_id=test_admin_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_client(db_session, test_user):
    """Provide an AsyncClient authenticated as a regular user."""
    from app.core.security import create_access_token

    async def override_get_db():
        yield db_session

    token = create_access_token(user_id=test_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Seed a test user in the database."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("password123"),
        display_name="Test User",
        native_language="vi",
        target_language="en",
        level="beginner",
        preferences={"is_admin": False}
    )
    db_session.add(user)
    await db_session.flush()
    
    # Add subscription
    sub = Subscription(user_id=user.id, tier="FREE", status="active")
    db_session.add(sub)
    await db_session.commit()
    
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin_user(db_session):
    """Seed a test admin user in the database."""
    user = User(
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        display_name="Admin User",
        native_language="en",
        target_language="vi",
        level="advanced",
        preferences={"is_admin": True}
    )
    db_session.add(user)
    await db_session.flush()
    
    # Add subscription
    sub = Subscription(user_id=user.id, tier="PRO", status="active")
    db_session.add(sub)
    await db_session.commit()
    
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_google_user(db_session):
    """Seed a Google-auth user without a password."""
    user = User(
        email="google@example.com",
        password_hash=None,
        auth_provider="google",
        display_name="Google User",
        native_language="vi",
        target_language="en",
        level="intermediate",
        preferences={"is_admin": False},
    )
    db_session.add(user)
    await db_session.flush()

    sub = Subscription(user_id=user.id, tier="FREE", status="active")
    db_session.add(sub)
    await db_session.commit()

    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_scenario(db_session):
    """Seed a test scenario."""
    from app.modules.scenarios.models.scenario import Scenario
    scenario = Scenario(
        title="Airport Check-in",
        description="A simple airport check-in scenario.",
        ai_system_prompt="You are a helpful airline agent.",
        category="travel",
        difficulty="medium",
        mode="roleplay",
        learning_objectives=["order food", "ask about specials"],
        target_skills=["pronunciation", "vocabulary"],
        tags=["airport", "travel"]
    )
    db_session.add(scenario)
    await db_session.flush()
    await db_session.refresh(scenario)
    return scenario


@pytest_asyncio.fixture
async def test_variation(db_session, test_scenario):
    """Seed a test variation."""
    from app.modules.scenarios.models.scenario import ScenarioVariation
    from app.modules.scenarios.services.variation_service import VariationService
    params = {"proficiency": "B1", "formality": "formal"}
    seed = VariationService.build_variation_seed(
        scenario_id=test_scenario.id,
        parameters=params,
        mode="roleplay"
    )
    variation = ScenarioVariation(
        scenario_id=test_scenario.id,
        variation_seed=seed,
        parameters=params,
        system_prompt_override="Variation prompt override.",
        is_pregenerated=True,
        is_approved=True
    )
    db_session.add(variation)
    await db_session.flush()
    await db_session.refresh(variation)
    return variation


@pytest_asyncio.fixture
async def test_session(db_session, test_user, test_scenario, test_variation):
    """Seed a test session."""
    from app.modules.sessions.models.session import Session
    session = Session(
        user_id=test_user.id,
        scenario_id=test_scenario.id,
        variation_id=test_variation.id,
        status="active",
        target_skills=test_scenario.target_skills,
        session_metadata={"mode": "roleplay", "variation_seed": test_variation.variation_seed}
    )
    db_session.add(session)
    await db_session.flush()
    await db_session.refresh(session)
    return session
