from typing import Any, Optional
import httpx

from ai.core.interfaces.provider import ILLMProvider
from ai.core.types.error import LLMError, LLMErrorType
from ai.core.types.request import LLMRequest
from ai.core.types.response import LLMFinishReason, LLMResponse, TokenUsage


class BaseOpenAICompatibleProvider(ILLMProvider):
    """Reusable foundation for any provider using the OpenAI Chat Completions API standard.

    Powers OpenAI, DeepSeek, OpenRouter, Kimi (Moonshot), Ollama, and self-hosted models.
    """

    def __init__(
        self,
        provider_id: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4o",
        custom_headers: Optional[dict[str, str]] = None,
        timeout: float = 60.0,
        client: Optional[httpx.AsyncClient] = None,
        requires_api_key: bool = True,
    ):
        self._provider_id = provider_id
        self._api_key = api_key or ""
        self._base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self._default_model = default_model
        self._custom_headers = custom_headers or {}
        self._timeout = timeout
        self._client = client
        self._requires_api_key = requires_api_key

    def get_provider_id(self) -> str:
        return self._provider_id

    def is_available(self) -> bool:
        if self._requires_api_key:
            return bool(self._api_key.strip())
        return bool(self._base_url.strip())

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if self._requires_api_key and not self.is_available():
            raise LLMError(
                error_type=LLMErrorType.AUTHENTICATION_FAILED,
                message=f"{self._provider_id} client not configured — valid API key required",
                provider_id=self._provider_id,
            )

        headers = {
            "Content-Type": "application/json",
            **self._custom_headers,
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        if request.extra_headers:
            headers.update(request.extra_headers)

        payload: dict[str, Any] = {
            "model": request.model or self._default_model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.extra_body:
            payload.update(request.extra_body)

        url = f"{self._base_url}/chat/completions"

        try:
            if self._client is not None:
                response = await self._client.post(
                    url, json=payload, headers=headers, timeout=self._timeout
                )
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

            return self._handle_response(response, request)

        except httpx.TimeoutException as exc:
            raise LLMError(
                error_type=LLMErrorType.TIMEOUT,
                message=f"Request to {self._provider_id} timed out after {self._timeout}s",
                provider_id=self._provider_id,
                original_error=exc,
            ) from exc
        except httpx.RequestError as exc:
            raise LLMError(
                error_type=LLMErrorType.PROVIDER_ERROR,
                message=f"Network communication failed with {self._provider_id}: {exc}",
                provider_id=self._provider_id,
                original_error=exc,
            ) from exc
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(
                error_type=LLMErrorType.UNKNOWN,
                message=f"Unexpected error communicating with {self._provider_id}: {exc}",
                provider_id=self._provider_id,
                original_error=exc,
            ) from exc

    def _handle_response(
        self, response: httpx.Response, request: LLMRequest
    ) -> LLMResponse:
        status = response.status_code

        if status >= 400:
            error_text = response.text
            try:
                err_data = response.json()
                msg = (
                    err_data.get("error", {}).get("message")
                    or err_data.get("message")
                    or error_text
                )
            except Exception:
                msg = error_text

            if status == 401:
                err_type = LLMErrorType.AUTHENTICATION_FAILED
            elif status == 429:
                err_type = LLMErrorType.RATE_LIMITED
            elif status == 404:
                err_type = LLMErrorType.MODEL_UNAVAILABLE
            elif status == 400:
                err_type = LLMErrorType.INVALID_REQUEST
            elif status in (500, 502, 503, 504):
                err_type = LLMErrorType.PROVIDER_ERROR
            else:
                err_type = LLMErrorType.UNKNOWN

            raise LLMError(
                error_type=err_type,
                message=f"{self._provider_id} API error ({status}): {msg}",
                provider_id=self._provider_id,
                original_error=response,
            )

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise LLMError(
                error_type=LLMErrorType.PROVIDER_ERROR,
                message=f"{self._provider_id} returned empty choices array",
                provider_id=self._provider_id,
            )

        choice = choices[0]
        content = choice.get("message", {}).get("content", "") or ""
        finish_reason = self._map_finish_reason(choice.get("finish_reason"))

        usage_dict = data.get("usage")
        usage = None
        if usage_dict:
            usage = TokenUsage(
                prompt_tokens=usage_dict.get("prompt_tokens", 0),
                completion_tokens=usage_dict.get("completion_tokens", 0),
                total_tokens=usage_dict.get("total_tokens", 0),
            )

        return LLMResponse(
            content=content,
            model=data.get("model", request.model),
            finish_reason=finish_reason,
            usage=usage,
            metadata={
                "id": data.get("id"),
                "created": data.get("created"),
            },
        )

    @staticmethod
    def _map_finish_reason(reason: Optional[str]) -> LLMFinishReason:
        if reason == "stop":
            return "stop"
        if reason == "length":
            return "length"
        if reason == "content_filter":
            return "content_filter"
        if reason == "tool_calls":
            return "tool_calls"
        return "unknown"
