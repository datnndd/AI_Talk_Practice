import pytest
from sqlalchemy import select

from app.core.config import DEFAULT_LLM_BASE_URL, Settings
from app.infra.factory import create_conversation_llm_clients, create_llm_for_role, LLMRole
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


def test_role_llm_config_falls_back_to_global_defaults():
    config = Settings(
        _env_file=None,
        llm_provider="openai",
        llm_model="global-model",
        llm_base_url="https://global.example/v1",
        openai_api_key="global-key",
        llm_temperature=0.4,
        llm_max_tokens=123,
    )

    llm = create_llm_for_role(config, LLMRole.DIALOGUE)

    assert llm._model == "global-model"
    assert str(llm._client.base_url) == "https://global.example/v1/"
    assert llm._config.llm_api_key == "global-key"
    assert llm._config.llm_temperature == 0.4
    assert llm._config.llm_max_tokens == 123


def test_role_llm_config_allows_different_models_and_providers():
    config = Settings(
        _env_file=None,
        llm_provider="openai",
        openai_api_key="global-key",
        analysis_llm_model="analysis-model",
        analysis_llm_base_url="https://analysis.example/v1",
        analysis_llm_api_key="analysis-key",
        analysis_llm_temperature=0.1,
        analysis_llm_max_tokens=321,
        dialogue_llm_model="dialogue-model",
        evaluation_llm_model="evaluation-model",
        evaluation_llm_base_url="https://evaluation.example/v1",
        evaluation_llm_api_key="evaluation-key",
    )

    clients = create_conversation_llm_clients(config)

    assert clients.analysis._model == "analysis-model"
    assert str(clients.analysis._client.base_url) == "https://analysis.example/v1/"
    assert clients.analysis._config.llm_api_key == "analysis-key"
    assert clients.analysis._config.llm_temperature == 0.1
    assert clients.analysis._config.llm_max_tokens == 321
    assert clients.dialogue._model == "dialogue-model"
    assert clients.evaluation._model == "evaluation-model"
    assert str(clients.evaluation._client.base_url) == "https://evaluation.example/v1/"


def test_role_llm_config_rejects_unsupported_provider():
    config = Settings(_env_file=None, analysis_llm_provider="unknown")

    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_llm_for_role(config, LLMRole.ANALYSIS)
