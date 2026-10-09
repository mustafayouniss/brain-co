from ai.config.ai_config import AIConfig
from ai.core.services.llm_service import LLMService
from ai.providers.deepseek_provider import DeepSeekProvider
from ai.providers.fake_provider import FakeLLMProvider
from ai.providers.kimi_provider import KimiProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.openrouter_provider import OpenRouterProvider


def test_ai_config_create_default_provider():
    config = AIConfig(AI_PROVIDER="openai", OPENAI_API_KEY="sk-test")
    provider = config.create_provider()
    assert isinstance(provider, OpenAIProvider)
    assert provider.get_provider_id() == "openai"


def test_ai_config_create_deepseek_provider():
    config = AIConfig(AI_PROVIDER="deepseek", DEEPSEEK_API_KEY="sk-deepseek")
    provider = config.create_provider()
    assert isinstance(provider, DeepSeekProvider)
    assert provider.get_provider_id() == "deepseek"


def test_ai_config_create_openrouter_provider():
    config = AIConfig(AI_PROVIDER="openrouter", OPENROUTER_API_KEY="sk-or")
    provider = config.create_provider()
    assert isinstance(provider, OpenRouterProvider)
    assert provider.get_provider_id() == "openrouter"


def test_ai_config_create_kimi_provider():
    config = AIConfig(AI_PROVIDER="kimi", KIMI_API_KEY="sk-kimi")
    provider = config.create_provider()
    assert isinstance(provider, KimiProvider)
    assert provider.get_provider_id() == "kimi"


def test_ai_config_create_ollama_provider():
    config = AIConfig(AI_PROVIDER="ollama")
    provider = config.create_provider()
    assert isinstance(provider, OllamaProvider)
    assert provider.get_provider_id() == "ollama"


def test_ai_config_create_fake_provider():
    config = AIConfig(AI_PROVIDER="fake")
    provider = config.create_provider()
    assert isinstance(provider, FakeLLMProvider)
    assert provider.get_provider_id() == "fake"


def test_ai_config_create_service():
    config = AIConfig(AI_PROVIDER="fake")
    service = config.create_service()
    assert isinstance(service, LLMService)
    assert service.get_provider().get_provider_id() == "fake"
