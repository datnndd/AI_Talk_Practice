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
from app.database import Base, get_db
from app.auth import hash_password
from app.models.user import User

# Use in-memory SQLite with StaticPool to keep connection open across sessions in tests
engine = create_async_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
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
async def test_user(db_session):
    """Seed a test user in the database."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("password123"),
        display_name="Test User",
        native_language="vi",
        target_language="en",
        level="beginner"
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user

