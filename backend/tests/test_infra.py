import pytest
from sqlalchemy import select
from app.models.user import User

@pytest.mark.asyncio
async def test_db_session(db_session):
    """Test that the database session works."""
    result = await db_session.execute(select(User))
    users = result.scalars().all()
    assert len(users) == 0

@pytest.mark.asyncio
async def test_test_user(test_user):
    """Test that the test_user fixture works."""
    assert test_user.email == "test@example.com"
