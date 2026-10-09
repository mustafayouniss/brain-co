import inspect
import pytest

from ai.core.interfaces.provider import ILLMProvider
from ai.providers.deepseek_provider import DeepSeekProvider
from ai.providers.fake_provider import FakeLLMProvider
from ai.providers.kimi_provider import KimiProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.openrouter_provider import OpenRouterProvider


@pytest.mark.parametrize(
    "provider_instance",
    [
        FakeLLMProvider(),
        OpenAIProvider(api_key="test-key"),
        DeepSeekProvider(api_key="test-key"),
        OpenRouterProvider(api_key="test-key"),
        KimiProvider(api_key="test-key"),
        OllamaProvider(),
    ],
)
def test_all_providers_satisfy_contract(provider_instance: ILLMProvider):
    # Must inherit from ILLMProvider
    assert isinstance(provider_instance, ILLMProvider)

    # get_provider_id must return a valid non-empty string
    provider_id = provider_instance.get_provider_id()
    assert isinstance(provider_id, str)
    assert len(provider_id.strip()) > 0

    # is_available must return a boolean
    available = provider_instance.is_available()
    assert isinstance(available, bool)

    # generate must be an async coroutine function
    assert inspect.iscoroutinefunction(provider_instance.generate)
