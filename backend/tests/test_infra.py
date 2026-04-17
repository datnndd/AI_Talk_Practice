import pytest
from sqlalchemy import select

from app.core.config import DEFAULT_LLM_BASE_URL, Settings
from app.modules.users.models.user import User

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


def test_llm_base_url_defaults_to_9router_endpoint():
    config = Settings(_env_file=None, llm_provider="openai")

    assert config.llm_base_url == DEFAULT_LLM_BASE_URL


def test_llm_base_url_allows_explicit_override():
    base_url = "https://example.test/v1"
    config = Settings(_env_file=None, llm_provider="openai", llm_base_url=base_url)

    assert config.llm_base_url == base_url
