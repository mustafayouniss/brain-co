import time
import uuid
from typing import Optional, Sequence

from ai.core.interfaces.provider import ILLMProvider
from ai.core.types.error import LLMError, LLMErrorType
from ai.core.types.request import LLMRequest
from ai.core.types.response import LLMResponse
from ai.utils.logger import ILogger, get_ai_logger


class LLMService:
    """Provider-agnostic LLM service with ordered provider failover.

    The configured primary provider is always tried first. When it fails with a
    provider-level error that may be recoverable by switching providers, the
    remaining configured providers are tried in order. This class does not
    implement streaming/resume yet; each attempt currently returns one complete
    response or an error.
    """

    _RETRYABLE_ERROR_TYPES = {
        LLMErrorType.AUTHENTICATION_FAILED,
        LLMErrorType.RATE_LIMITED,
        LLMErrorType.MODEL_UNAVAILABLE,
        LLMErrorType.TIMEOUT,
        LLMErrorType.PROVIDER_ERROR,
        LLMErrorType.UNKNOWN,
    }

    def __init__(
        self,
        provider: ILLMProvider,
        fallback_providers: Optional[Sequence[ILLMProvider]] = None,
        logger: Optional[ILogger] = None,
    ):
        self._provider = provider
        self._fallback_providers = list(fallback_providers or [])
        self._logger = logger or get_ai_logger()

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Run the request, moving to configured fallback providers when appropriate."""
        correlation_id = self._generate_correlation_id()
        request_start = time.perf_counter()
        providers = self._ordered_providers()
        last_error: Optional[LLMError] = None

        self._logger.info({
            "event": "llm_request_started",
            "correlationId": correlation_id,
            "provider": self._provider.get_provider_id(),
            "fallbackProviders": [p.get_provider_id() for p in providers[1:]],
            "model": request.model,
            "messageCount": len(request.messages),
        })

        for attempt_index, provider in enumerate(providers):
            provider_id = provider.get_provider_id()
            is_fallback = attempt_index > 0

            try:
                configured = provider.is_available()
            except Exception as exc:
                normalized = self._normalize_error(exc, provider)
                configured = False
                last_error = normalized
                self._logger.warning({
                    "event": "llm_provider_availability_check_failed",
                    "correlationId": correlation_id,
                    "provider": provider_id,
                    "errorType": normalized.error_type.value,
                    "errorMessage": normalized.message,
                })

            if not configured:
                self._logger.warning({
                    "event": "llm_provider_skipped",
                    "correlationId": correlation_id,
                    "provider": provider_id,
                    "reason": "provider_not_configured_or_unavailable",
                    "attempt": attempt_index + 1,
                })
                continue

            attempt_start = time.perf_counter()
            try:
                response = await provider.generate(request)
                attempt_latency_ms = int((time.perf_counter() - attempt_start) * 1000)
                total_latency_ms = int((time.perf_counter() - request_start) * 1000)

                self._logger.info({
                    "event": "llm_request_completed",
                    "correlationId": correlation_id,
                    "provider": provider_id,
                    "model": response.model,
                    "latency": attempt_latency_ms,
                    "totalLatency": total_latency_ms,
                    "usage": response.usage.model_dump() if response.usage else None,
                    "finishReason": response.finish_reason,
                    "fallbackUsed": is_fallback,
                    "attempt": attempt_index + 1,
                })
                return response

            except Exception as exc:
                normalized = self._normalize_error(exc, provider)
                last_error = normalized
                attempt_latency_ms = int((time.perf_counter() - attempt_start) * 1000)

                self._logger.error({
                    "event": "llm_provider_attempt_failed",
                    "correlationId": correlation_id,
                    "provider": provider_id,
                    "model": request.model,
                    "latency": attempt_latency_ms,
                    "errorType": normalized.error_type.value,
                    "errorMessage": normalized.message,
                    "attempt": attempt_index + 1,
                })

                has_next = attempt_index < len(providers) - 1
                if not has_next or normalized.error_type not in self._RETRYABLE_ERROR_TYPES:
                    # Keep the historical request-level failure event for callers/tests.
                    self._logger.error({
                        "event": "llm_request_failed",
                        "correlationId": correlation_id,
                        "provider": provider_id,
                        "model": request.model,
                        "latency": int((time.perf_counter() - request_start) * 1000),
                        "errorType": normalized.error_type.value,
                        "errorMessage": normalized.message,
                    })
                    # Preserve the normalized error and stop for non-retryable failures.
                    if normalized is exc:
                        raise
                    raise normalized from exc

                self._logger.warning({
                    "event": "llm_fallback_started",
                    "correlationId": correlation_id,
                    "failedProvider": provider_id,
                    "nextProvider": providers[attempt_index + 1].get_provider_id(),
                    "errorType": normalized.error_type.value,
                    "attempt": attempt_index + 2,
                })

        if last_error is not None:
            self._logger.error({
                "event": "llm_request_failed",
                "correlationId": correlation_id,
                "provider": last_error.provider_id or self._provider.get_provider_id(),
                "model": request.model,
                "latency": int((time.perf_counter() - request_start) * 1000),
                "errorType": last_error.error_type.value,
                "errorMessage": last_error.message,
            })
            raise last_error

        final_error = LLMError(
            error_type=LLMErrorType.AUTHENTICATION_FAILED,
            message="No configured AI providers are available. Check provider credentials and AI_FALLBACK_PROVIDERS.",
            provider_id=self._provider.get_provider_id(),
        )
        self._logger.error({
            "event": "llm_request_failed",
            "correlationId": correlation_id,
            "provider": final_error.provider_id,
            "model": request.model,
            "latency": int((time.perf_counter() - request_start) * 1000),
            "errorType": final_error.error_type.value,
            "errorMessage": final_error.message,
        })
        raise final_error

    def get_provider(self) -> ILLMProvider:
        """Return the configured primary provider."""
        return self._provider

    def get_fallback_providers(self) -> list[ILLMProvider]:
        """Return a copy of the ordered fallback provider list."""
        return list(self._fallback_providers)

    def set_provider(self, provider: ILLMProvider) -> None:
        """Replace the primary provider without changing higher-level callers."""
        self._provider = provider
        self._logger.info({
            "event": "llm_provider_changed",
            "newProvider": provider.get_provider_id(),
        })

    def _ordered_providers(self) -> list[ILLMProvider]:
        """Return providers in configured order, avoiding duplicate provider IDs."""
        ordered: list[ILLMProvider] = []
        seen: set[str] = set()
        for candidate in [self._provider, *self._fallback_providers]:
            provider_id = candidate.get_provider_id().strip().lower()
            if provider_id in seen:
                continue
            seen.add(provider_id)
            ordered.append(candidate)
        return ordered

    @staticmethod
    def _normalize_error(error: Exception, provider: ILLMProvider) -> LLMError:
        """Normalize provider exceptions and attach their actual provider ID."""
        provider_id = provider.get_provider_id()
        if isinstance(error, LLMError):
            if error.provider_id:
                return error
            return LLMError(
                error_type=error.error_type,
                message=error.message,
                provider_id=provider_id,
                original_error=error.original_error or error,
            )

        return LLMError(
            error_type=LLMErrorType.UNKNOWN,
            message=str(error) or "Unknown error",
            provider_id=provider_id,
            original_error=error,
        )

    @staticmethod
    def _generate_correlation_id() -> str:
        timestamp_ms = int(time.time() * 1000)
        suffix = uuid.uuid4().hex[:7]
        return f"llm_{timestamp_ms}_{suffix}"
