import time
import uuid
from typing import Optional

from ai.core.interfaces.provider import ILLMProvider
from ai.core.types.error import LLMError, LLMErrorType
from ai.core.types.request import LLMRequest
from ai.core.types.response import LLMResponse
from ai.utils.logger import ILogger, get_ai_logger


class LLMService:
    """Provider-agnostic LLM service.

    This is the primary orchestration entrypoint for all higher-level Brain rings.
    Higher rings interact exclusively with this service, remaining completely decoupled
    from whether requests are served by OpenAI, DeepSeek, OpenRouter, Kimi, Ollama, or mocks.
    """

    def __init__(self, provider: ILLMProvider, logger: Optional[ILogger] = None):
        self._provider = provider
        self._logger = logger or get_ai_logger()

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Asynchronously execute an LLM completion using the active provider.

        Tracks latency, assigns request correlation IDs, emits structured lifecycle logs,
        and normalizes exceptions into LLMError.
        """
        correlation_id = self._generate_correlation_id()
        start_time = time.perf_counter()

        self._logger.info({
            "event": "llm_request_started",
            "correlationId": correlation_id,
            "provider": self._provider.get_provider_id(),
            "model": request.model,
            "messageCount": len(request.messages),
        })

        try:
            response = await self._provider.generate(request)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            self._logger.info({
                "event": "llm_request_completed",
                "correlationId": correlation_id,
                "provider": self._provider.get_provider_id(),
                "model": response.model,
                "latency": latency_ms,
                "usage": response.usage.model_dump() if response.usage else None,
                "finishReason": response.finish_reason,
            })

            return response

        except Exception as exc:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            normalized = self._normalize_error(exc)

            self._logger.error({
                "event": "llm_request_failed",
                "correlationId": correlation_id,
                "provider": self._provider.get_provider_id(),
                "model": request.model,
                "latency": latency_ms,
                "errorType": normalized.error_type.value,
                "errorMessage": normalized.message,
            })

            raise normalized from exc

    def get_provider(self) -> ILLMProvider:
        """Return the currently active LLM provider."""
        return self._provider

    def set_provider(self, provider: ILLMProvider) -> None:
        """Swap the active provider at runtime without altering higher-level ring state."""
        self._provider = provider
        self._logger.info({
            "event": "llm_provider_changed",
            "newProvider": provider.get_provider_id(),
        })

    def _normalize_error(self, error: Exception) -> LLMError:
        """Ensure any unhandled exception is wrapped in a standardized LLMError."""
        if isinstance(error, LLMError):
            return error

        return LLMError(
            error_type=LLMErrorType.UNKNOWN,
            message=str(error) or "Unknown error",
            provider_id=self._provider.get_provider_id(),
            original_error=error,
        )

    @staticmethod
    def _generate_correlation_id() -> str:
        """Generate a unique tracking identifier for the request."""
        timestamp_ms = int(time.time() * 1000)
        suffix = uuid.uuid4().hex[:7]
        return f"llm_{timestamp_ms}_{suffix}"
