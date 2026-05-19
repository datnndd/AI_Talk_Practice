import pytest
from sqlalchemy import select

from app.core.config import DEFAULT_LLM_BASE_URL, Settings
from app.infra.contracts import Message
from app.infra.factory import create_conversation_llm_clients, create_llm_for_role, LLMRole
from app.infra.llm.openai_llm import OpenAILLM
from app.modules.users.models.user import User

class FakeStreamResponse:
    def __init__(self, lines):
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        return None

    async def aiter_lines(self):
        for line in self._lines:
            yield line

class FakeOpenAIClient:
    def __init__(self, lines):
        self.lines = lines
        self.requests = []

    def stream(self, method, path, json):
        self.requests.append({"method": method, "path": path, "json": json})
        return FakeStreamResponse(self.lines)

    async def aclose(self):
        return None

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

@pytest.mark.asyncio
async def test_openai_llm_uses_chat_completions_stream_payload():
    config = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        frontend_url="http://localhost:5173",
        cors_origins=["*"],
        llm_provider="openai",
        llm_model="test-model",
        llm_base_url="https://example.test/v1",
        openai_api_key="test-key",
        llm_temperature=0.2,
        llm_max_tokens=99,
    )
    llm = OpenAILLM(config)
    fake_client = FakeOpenAIClient(
        [
            'data: {"choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{"content":" there."},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}',
            "data: [DONE]",
        ]
    )
    await llm._client.aclose()
    llm._client = fake_client

    chunks = [
        chunk
        async for chunk in llm.chat_stream(
            [Message(role="user", content="Hi")],
            system_prompt="You are helpful.",
            max_tokens=42,
        )
    ]

    assert chunks == ["Hello", " there."]
    assert len(fake_client.requests) == 1
    request = fake_client.requests[0]
    assert request["method"] == "POST"
    assert request["path"] == "/chat/completions"

    payload = request["json"]
    assert payload["model"] == "test-model"
    assert payload["stream"] is True
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 42
    assert "max_output_tokens" not in payload
    assert "input" not in payload
    assert "instructions" not in payload
    assert payload["messages"] == [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hi"},
    ]
