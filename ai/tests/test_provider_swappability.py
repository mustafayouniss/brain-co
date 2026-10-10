import asyncio
import pytest

from ai.core.services.llm_service import LLMService
from ai.core.types.request import LLMMessage, LLMRequest
from ai.providers.deepseek_provider import DeepSeekProvider
from ai.providers.fake_provider import FakeLLMProvider
from ai.providers.kimi_provider import KimiProvider
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.openrouter_provider import OpenRouterProvider
from ai.providers.registry import ProviderRegistry


def test_should_work_with_initial_provider():
    """Verify LLMService executes requests with its initial provider."""
    provider = FakeLLMProvider(custom_response="Initial response")
    service = LLMService(provider=provider)

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model="fake-model",
    )

    response = asyncio.run(service.generate(request))
    assert response.content == "Initial response"
    assert response.model == "fake-model"
    assert len(provider.recorded_requests) == 1


def test_should_work_after_swapping_provider():
    """Verify swapping the provider redirects requests to the new provider."""
    provider1 = FakeLLMProvider(custom_response="Response from Provider 1")
    provider2 = FakeLLMProvider(custom_response="Response from Provider 2")

    service = LLMService(provider=provider1)

    req = LLMRequest(
        messages=[LLMMessage(role="user", content="Test")],
        model="model-1",
    )

    res1 = asyncio.run(service.generate(req))
    assert res1.content == "Response from Provider 1"

    # Swap to provider2
    service.set_provider(provider2)

    res2 = asyncio.run(service.generate(req))
    assert res2.content == "Response from Provider 2"
    assert len(provider1.recorded_requests) == 1
    assert len(provider2.recorded_requests) == 1


def test_should_not_require_changes_to_higher_level_code_when_swapping():
    """Verify high-level consumer functions require zero changes when providers change."""
    async def higher_level_ring_business_logic(svc: LLMService) -> str:
        # Ring 7 / Legal Assistance logic
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Analyze legal case facts")],
            model="target-model",
        )
        res = await svc.generate(request)
        return res.content

    fake1 = FakeLLMProvider(custom_response="Analysis from Model A")
    fake2 = FakeLLMProvider(custom_response="Analysis from Model B")

    service = LLMService(provider=fake1)
    result_a = asyncio.run(higher_level_ring_business_logic(service))
    assert result_a == "Analysis from Model A"

    service.set_provider(fake2)
    result_b = asyncio.run(higher_level_ring_business_logic(service))
    assert result_b == "Analysis from Model B"


def test_should_maintain_service_interface_after_provider_swap():
    """Verify service interface integrity is preserved across multiple swaps."""
    p1 = FakeLLMProvider(custom_response="R1")
    p2 = FakeLLMProvider(custom_response="R2")
    service = LLMService(provider=p1)

    assert service.get_provider().get_provider_id() == "fake"
    service.set_provider(p2)
    assert service.get_provider().get_provider_id() == "fake"


def test_should_allow_swapping_between_different_provider_types():
    """Verify swapping between different real provider classes (OpenAI, DeepSeek, Kimi, OpenRouter)."""
    fake = FakeLLMProvider(custom_response="Fake output")
    openai_p = OpenAIProvider(api_key="sk-test", base_url="http://mock.openai")
    deepseek_p = DeepSeekProvider(api_key="sk-test", base_url="http://mock.deepseek")
    openrouter_p = OpenRouterProvider(api_key="sk-test", base_url="http://mock.openrouter")
    kimi_p = KimiProvider(api_key="sk-test", base_url="http://mock.kimi")

    service = LLMService(provider=fake)
    assert service.get_provider().get_provider_id() == "fake"

    service.set_provider(openai_p)
    assert service.get_provider().get_provider_id() == "openai"

    service.set_provider(deepseek_p)
    assert service.get_provider().get_provider_id() == "deepseek"

    service.set_provider(openrouter_p)
    assert service.get_provider().get_provider_id() == "openrouter"

    service.set_provider(kimi_p)
    assert service.get_provider().get_provider_id() == "kimi"
