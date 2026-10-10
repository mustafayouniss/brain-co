import asyncio
import json
import httpx
import pytest

from ai.core.interfaces.provider import ILLMProvider
from ai.core.types.error import LLMError, LLMErrorType
from ai.core.types.request import LLMMessage, LLMRequest
from ai.providers.deepseek_provider import DeepSeekProvider
from ai.providers.kimi_provider import KimiProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.openrouter_provider import OpenRouterProvider
from ai.providers.registry import ProviderRegistry


def test_openai_provider_initialization():
    p_with_key = OpenAIProvider(api_key="sk-test-key")
    assert p_with_key.get_provider_id() == "openai"
    assert p_with_key.is_available() is True

    p_no_key = OpenAIProvider(api_key="")
    assert p_no_key.is_available() is False


def test_deepseek_provider_configuration():
    p = DeepSeekProvider(api_key="sk-deepseek-key")
    assert p.get_provider_id() == "deepseek"
    assert p.is_available() is True
    assert p._base_url == "https://api.deepseek.com"
    assert p._default_model == "deepseek-chat"


def test_openrouter_provider_configuration():
    p = OpenRouterProvider(
        api_key="sk-or-key",
        site_url="https://example.com",
        site_name="TestApp",
    )
    assert p.get_provider_id() == "openrouter"
    assert p.is_available() is True
    assert p._base_url == "https://openrouter.ai/api/v1"
    assert p._custom_headers.get("HTTP-Referer") == "https://example.com"
    assert p._custom_headers.get("X-Title") == "TestApp"


def test_kimi_provider_configuration():
    p = KimiProvider(api_key="sk-kimi-key")
    assert p.get_provider_id() == "kimi"
    assert p.is_available() is True
    assert p._base_url == "https://api.moonshot.cn/v1"
    assert p._default_model == "moonshot-v1-8k"


def test_ollama_provider_configuration():
    p = OllamaProvider()
    assert p.get_provider_id() == "ollama"
    # Ollama is available without needing an external API key
    assert p.is_available() is True
    assert p._base_url == "http://localhost:11434/v1"
    assert p._default_model == "llama3"


def test_provider_registry_listing_and_creation():
    available = ProviderRegistry.list_providers()
    assert "openai" in available
    assert "deepseek" in available
    assert "openrouter" in available
    assert "kimi" in available
    assert "ollama" in available
    assert "fake" in available

    instance = ProviderRegistry.create("deepseek", api_key="sk-test")
    assert isinstance(instance, DeepSeekProvider)
    assert instance.get_provider_id() == "deepseek"


def test_provider_registry_unknown_provider_raises_error():
    with pytest.raises(LLMError) as exc_info:
        ProviderRegistry.create("non_existent_provider")

    assert exc_info.value.error_type == LLMErrorType.INVALID_REQUEST
    assert "Unknown LLM provider" in exc_info.value.message


def test_provider_registry_dynamic_registration():
    class CustomEnterpriseProvider(ILLMProvider):
        def __init__(self, endpoint: str = "http://enterprise.local"):
            self.endpoint = endpoint

        def get_provider_id(self) -> str:
            return "custom_enterprise"

        def is_available(self) -> bool:
            return True

        async def generate(self, request: LLMRequest):
            raise NotImplementedError()

    ProviderRegistry.register("custom_enterprise", CustomEnterpriseProvider)
    assert ProviderRegistry.is_registered("custom_enterprise")

    created = ProviderRegistry.create("custom_enterprise", endpoint="http://custom.local")
    assert created.get_provider_id() == "custom_enterprise"


def test_mock_client_response_handling_success():
    """Verify response parsing using a mock httpx transport."""
    mock_response_data = {
        "id": "chatcmpl-123",
        "created": 1677652288,
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Mocked legal answer"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 8,
            "total_tokens": 20,
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response_data)

    transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=transport)

    provider = DeepSeekProvider(api_key="sk-test", client=mock_client)
    req = LLMRequest(
        messages=[LLMMessage(role="user", content="Question")],
        model="deepseek-chat",
    )

    res = asyncio.run(provider.generate(req))
    assert res.content == "Mocked legal answer"
    assert res.model == "deepseek-chat"
    assert res.finish_reason == "stop"
    assert res.usage is not None
    assert res.usage.total_tokens == 20


def test_mock_client_response_handling_rate_limit_error():
    """Verify HTTP 429 is mapped to LLMErrorType.RATE_LIMITED."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "Rate limit exceeded"}})

    transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=transport)

    provider = OpenAIProvider(api_key="sk-test", client=mock_client)
    req = LLMRequest(
        messages=[LLMMessage(role="user", content="Question")],
        model="gpt-4o",
    )

    with pytest.raises(LLMError) as exc_info:
        asyncio.run(provider.generate(req))

    assert exc_info.value.error_type == LLMErrorType.RATE_LIMITED
    assert "Rate limit exceeded" in exc_info.value.message
