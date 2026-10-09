from abc import ABC, abstractmethod

from ai.core.types.request import LLMRequest
from ai.core.types.response import LLMResponse


class ILLMProvider(ABC):
    """Abstract interface defining the contract for any LLM provider.

    All LLM providers (OpenAI, DeepSeek, OpenRouter, Kimi, Ollama, Fake, etc.)
    must implement this interface. Higher-level rings depend exclusively on this
    contract and never on provider-specific SDKs.
    """

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Asynchronously generate a completion for the given request.

        Args:
            request: Provider-independent LLM request.

        Returns:
            Normalized LLM response.

        Raises:
            LLMError: Standardized error representation. Provider-specific exceptions
                must never leak outside the implementation.
        """
        pass

    @abstractmethod
    def get_provider_id(self) -> str:
        """Return the unique provider identifier (e.g. 'openai', 'deepseek', 'openrouter', 'kimi')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured (e.g. valid API key/endpoint present)."""
        pass
