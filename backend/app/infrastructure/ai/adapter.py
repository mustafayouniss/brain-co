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

DEFAULT_BACKEND_MODEL = "gpt-4o-mini"


class LLMServiceAdapter(ILLMClient):
    """Adapter bridging Backend LLMService to General Brain ILLMClient."""

    def __init__(
        self,
        llm_service: LLMService,
        default_model: str = DEFAULT_BACKEND_MODEL,
    ) -> None:
        self._llm_service = llm_service
        self._default_model = default_model

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Execute completion via Backend LLMService."""
        try:
            # Map model hint or fall back to default backend configured model
            target_model = self._default_model
            if request.model_hint:
                if request.model_hint == "reasoning":
                    target_model = "o3-mini"
                elif request.model_hint == "fast":
                    target_model = "gpt-4o-mini"

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
