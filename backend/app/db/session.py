"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

is_sqlite = settings.database_url.startswith("sqlite")

if is_sqlite:
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.types import JSON
    postgresql.JSONB = JSON

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_debug,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if is_sqlite else {},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a managed async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
