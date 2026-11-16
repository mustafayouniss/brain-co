"""AI Service Adapter implementing General Brain ILLMClient protocol.

Bridges General Brain's provider-agnostic ILLMClient contract to Backend's
ai.core LLMService orchestration layer. General Brain remains 100% free of
ai.core dependencies and vendor model hardcoding.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ai.core.services.llm_service import LLMService
from ai.core.types.request import LLMMessage as BackendLLMMessage
from ai.core.types.request import LLMRequest as BackendLLMRequest
from brain.general.contracts.llm import (
    ILLMClient,
    LLMClientError,
    LLMRequest,
    LLMResponse,
)

logger = logging.getLogger("app.infrastructure.ai.adapter")

DEFAULT_BACKEND_MODEL = "gemini-3.5-flash-lite"


class LLMServiceAdapter(ILLMClient):
    """Adapter bridging Backend LLMService to General Brain ILLMClient."""

    def __init__(
        self,
        llm_service: LLMService,
        default_model: Optional[str] = None,
    ) -> None:
        self._llm_service = llm_service
        provider = getattr(llm_service, "_provider", None)
        provider_model = getattr(provider, "_default_model", None) if provider else None
        self._default_model = default_model or provider_model or DEFAULT_BACKEND_MODEL

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Execute completion via Backend LLMService."""
        try:
            # Map model hint or fall back to default backend configured model
            provider = getattr(self._llm_service, "_provider", None)
            provider_id = provider.get_provider_id() if provider and hasattr(provider, "get_provider_id") else ""
            target_model = self._default_model
            if request.model_hint:
                if provider_id == "gemini":
                    target_model = self._default_model
                elif provider_id == "deepseek":
                    if request.model_hint == "reasoning":
                        target_model = "deepseek-reasoner"
                    elif request.model_hint == "fast":
                        target_model = "deepseek-chat"
                else:
                    target_model = self._default_model

            backend_messages = [
                BackendLLMMessage(
                    role=msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                    content=msg.content,
                )
                for msg in request.messages
            ]

            backend_req = BackendLLMRequest(
                messages=backend_messages,
                model=target_model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            backend_resp = await self._llm_service.generate(backend_req)

            return LLMResponse(
                content=backend_resp.content,
                model_identifier=backend_resp.model,
                finish_reason=backend_resp.finish_reason,
                metadata={"usage": backend_resp.usage.model_dump() if backend_resp.usage else {}},
            )
        except Exception as exc:
            logger.error("LLMServiceAdapter completion failed: %s", exc)
            raise LLMClientError(
                message=f"LLM completion error: {exc}",
                is_retryable=False,
                detail={"underlying_error": str(exc)},
            ) from exc


__all__ = ["LLMServiceAdapter"]
