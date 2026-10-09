from typing import Optional

from ai.core.interfaces.provider import ILLMProvider
from ai.core.types.error import LLMError
from ai.core.types.request import LLMRequest
from ai.core.types.response import LLMFinishReason, LLMResponse, TokenUsage


class FakeLLMProvider(ILLMProvider):
    """Deterministic, zero-cost fake provider for unit testing and CI/CD pipelines."""

    def __init__(
        self,
        custom_response: str = "Test response from FakeLLMProvider",
        finish_reason: LLMFinishReason = "stop",
        prompt_tokens: int = 10,
        completion_tokens: int = 5,
        available: bool = True,
        forced_error: Optional[Exception] = None,
    ):
        self._provider_id = "fake"
        self._custom_response = custom_response
        self._finish_reason = finish_reason
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self._available = available
        self._forced_error = forced_error
        self.recorded_requests: list[LLMRequest] = []

    def get_provider_id(self) -> str:
        return self._provider_id

    def is_available(self) -> bool:
        return self._available

    def set_available(self, available: bool) -> None:
        self._available = available

    def set_custom_response(self, response: str) -> None:
        self._custom_response = response

    def set_forced_error(self, error: Optional[Exception]) -> None:
        self._forced_error = error

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.recorded_requests.append(request)

        if self._forced_error is not None:
            raise self._forced_error

        return LLMResponse(
            content=self._custom_response,
            model=request.model,
            finish_reason=self._finish_reason,
            usage=TokenUsage(
                prompt_tokens=self._prompt_tokens,
                completion_tokens=self._completion_tokens,
                total_tokens=self._prompt_tokens + self._completion_tokens,
            ),
            metadata={"mock": True, "call_count": len(self.recorded_requests)},
        )
