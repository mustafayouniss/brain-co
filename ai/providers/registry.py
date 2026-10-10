
from typing import Any, Callable, Optional, Type

from ai.core.interfaces.provider import ILLMProvider
from ai.core.types.error import LLMError, LLMErrorType
from ai.providers.deepseek_provider import DeepSeekProvider
from ai.providers.fake_provider import FakeLLMProvider
from ai.providers.kimi_provider import KimiProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.openrouter_provider import OpenRouterProvider
from ai.providers.groq_provider import GroqProvider
from ai.providers.huggingface_provider import HuggingFaceProvider


class ProviderRegistry:
    """Central provider registry and factory.

    Enables dynamic registration and instantiation of any LLM provider.
    Higher-level rings instantiate providers solely through this factory,
    ensuring zero code modifications when adding or switching providers.
    """

    _registry: dict[str, Type[ILLMProvider]] = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "openrouter": OpenRouterProvider,
        "kimi": KimiProvider,
        "moonshot": KimiProvider,
        "ollama": OllamaProvider,
        "groq": GroqProvider,
        "huggingface": HuggingFaceProvider,
        "hf": HuggingFaceProvider,
        "fake": FakeLLMProvider,
    }

    @classmethod
    def register(cls, provider_id: str, provider_cls: Type[ILLMProvider]) -> None:
        """Register a new LLM provider type into the registry."""
        normalized_id = provider_id.strip().lower()
        cls._registry[normalized_id] = provider_cls

    @classmethod
    def is_registered(cls, provider_id: str) -> bool:
        """Check if a provider ID exists in the registry."""
        return provider_id.strip().lower() in cls._registry

    @classmethod
    def list_providers(cls) -> list[str]:
        """Return list of all registered provider IDs."""
        return sorted(list(cls._registry.keys()))

    @classmethod
    def create(cls, provider_id: str, **kwargs: Any) -> ILLMProvider:
        """Instantiate a provider by its unique identifier.

        Args:
            provider_id: The provider identifier ('openai', 'deepseek', 'openrouter', 'kimi', etc.)
            **kwargs: Configuration arguments passed to the provider's constructor.

        Returns:
            An instance implementing ILLMProvider.

        Raises:
            LLMError: If provider_id is not registered.
        """
        normalized_id = provider_id.strip().lower()
        provider_cls = cls._registry.get(normalized_id)

        if provider_cls is None:
            available = ", ".join(cls.list_providers())
            raise LLMError(
                error_type=LLMErrorType.INVALID_REQUEST,
                message=f"Unknown LLM provider '{provider_id}'. Available providers: [{available}]",
                provider_id=provider_id,
            )

        return provider_cls(**kwargs)