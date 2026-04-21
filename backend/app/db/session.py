"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator
import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

is_sqlite = settings.database_url.startswith("sqlite")
logger = logging.getLogger(__name__)

if is_sqlite:
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.types import JSON
    # Mock JSONB for SQLite compatibility
    setattr(postgresql, "JSONB", JSON)
    import sys
    # Also ensure any direct imports of JSONB from the module are redirected
    if "sqlalchemy.dialects.postgresql.json" in sys.modules:
        setattr(sys.modules["sqlalchemy.dialects.postgresql.json"], "JSONB", JSON)
    if "sqlalchemy.dialects.postgresql" in sys.modules:
        setattr(sys.modules["sqlalchemy.dialects.postgresql"], "JSONB", JSON)

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


def _ensure_sqlite_schema_compatibility_sync(sync_conn) -> None:
    inspector = inspect(sync_conn)
    if "scenarios" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("scenarios")}
    missing_columns = []

    compatibility_columns = (
        ("ai_role", "VARCHAR(500) DEFAULT '' NOT NULL"),
        ("user_role", "VARCHAR(500) DEFAULT '' NOT NULL"),
        ("time_limit_minutes", "INTEGER"),
    )

    for column_name, column_sql in compatibility_columns:
        if column_name in existing_columns:
            continue
        sync_conn.execute(text(f"ALTER TABLE scenarios ADD COLUMN {column_name} {column_sql}"))
        missing_columns.append(column_name)

    if missing_columns:
        logger.warning(
            "Auto-repaired SQLite schema for scenarios table; added missing columns: %s",
            ", ".join(missing_columns),
        )


async def ensure_sqlite_schema_compatibility() -> None:
    """Backfill legacy SQLite dev databases that missed scenario columns."""
    if not is_sqlite:
        return

    async with engine.begin() as conn:
        await conn.run_sync(_ensure_sqlite_schema_compatibility_sync)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a managed async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
