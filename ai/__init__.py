"""Organizational Brain — AI Engine (Python 3.12).

Provider-agnostic, async-first AI foundation layer.
Supports OpenAI, DeepSeek, OpenRouter, Kimi (Moonshot), Ollama, and Fake testing provider.
"""

from ai.core.interfaces.provider import ILLMProvider
from ai.core.services.llm_service import LLMService
from ai.core.types.error import LLMError, LLMErrorType
from ai.core.types.request import LLMMessage, LLMRequest
from ai.core.types.response import LLMFinishReason, LLMResponse, TokenUsage
from ai.prompts.prompt_template import PromptTemplate
from ai.providers.registry import ProviderRegistry

__all__ = [
    "ILLMProvider",
    "LLMService",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "TokenUsage",
    "LLMFinishReason",
    "LLMError",
    "LLMErrorType",
    "PromptTemplate",
    "ProviderRegistry",
]
