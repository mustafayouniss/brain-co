"""Base engine class implementing the Intelligence Layer + Deterministic Core pattern.

Every Ring 1 engine inherits from BaseEngine. The base class provides:
- Capability registration with the mesh registry.
- Request validation (protocol version, context ref, constraints).
- The decision order: validate → check context → try deterministic → use LLM → validate LLM output → delegate or return.
- Safe error wrapping so engines never leak raw stack traces.
- LLM integration via the existing LLMService abstraction.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from ai.core.interfaces.provider import ILLMProvider
from ai.core.services.llm_service import LLMService
from ai.core.types.error import LLMError
from ai.core.types.request import LLMMessage, LLMRequest
from ai.core.types.response import LLMResponse

from app.ring1.contracts.capabilities import CapabilityRegistry
from app.ring1.contracts.envelopes import (
    PROTOCOL_VERSION,
    MeshError,
    MeshRequest,
    MeshResponse,
    ResultStatus,
)
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.mesh.router import MeshRouter


class BaseEngine(ABC):
    """Abstract base for all Ring 1 engines.

    Subclasses must implement:
    - engine_name: property returning the engine identifier
    - register_capabilities(registry): register handlers with the capability registry
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        mesh_router: Optional[MeshRouter] = None,
    ) -> None:
        self._llm_service = llm_service
        self._mesh_router = mesh_router
        self._logger = logging.getLogger(f"ring1.{self.engine_name}")

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Unique identifier for this engine (e.g. 'perception', 'observation')."""
        ...

    @abstractmethod
    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        """Register this engine's capability handlers with the shared registry."""
        ...

    # -----------------------------------------------------------------
    # Validation helpers (deterministic core)
    # -----------------------------------------------------------------

    def validate_request(self, request: MeshRequest) -> Optional[MeshResponse]:
        """Run standard request validation. Returns an error response or None if valid.

        Checks performed:
        1. Protocol version
        2. Delegation depth remaining
        """
        if request.protocol_version != PROTOCOL_VERSION:
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.UNSUPPORTED_PROTOCOL_VERSION,
                f"Expected protocol version '{PROTOCOL_VERSION}', "
                f"got '{request.protocol_version}'.",
            )
        if request.constraints.max_delegations_remaining <= 0:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.DELEGATION_DEPTH_EXCEEDED,
                "Delegation depth exceeded.",
            )
        return None

    def require_context_ref(self, request: MeshRequest) -> Optional[MeshResponse]:
        """Return an error response if context_ref is missing. Returns None if present."""
        if not request.context_ref:
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "context_ref is required for this operation.",
            )
        return None

    # -----------------------------------------------------------------
    # Intelligence Layer: LLM interaction
    # -----------------------------------------------------------------

    async def _call_llm(
        self,
        system_prompt: str,
        user_content: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """Call the LLM via the shared LLMService.

        Returns the response content string, or None if the LLM is unavailable
        or returns an error. Never raises — errors are logged and None is returned
        for the caller to handle with a deterministic fallback.
        """
        if self._llm_service is None:
            self._logger.warning("LLM service not configured; skipping LLM call.")
            return None

        try:
            llm_request = LLMRequest(
                messages=[
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=user_content),
                ],
                model=model or "gpt-4o-mini",
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response: LLMResponse = await self._llm_service.generate(llm_request)
            return response.content
        except LLMError as exc:
            self._logger.warning(
                "LLM call failed: %s", exc.message,
                extra={"engine": self.engine_name, "error_type": exc.error_type.value},
            )
            return None
        except Exception as exc:
            self._logger.warning(
                "Unexpected LLM error: %s", str(exc),
                extra={"engine": self.engine_name},
            )
            return None

    async def _call_llm_json(
        self,
        system_prompt: str,
        user_content: str,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """Call the LLM and attempt to parse the response as JSON.

        Returns a dict on success, or None if the LLM fails or returns
        non-JSON content.
        """
        raw = await self._call_llm(system_prompt, user_content, **kwargs)
        if raw is None:
            return None
        try:
            # Strip markdown code fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines)
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError) as exc:
            self._logger.warning(
                "LLM returned non-JSON output: %s", str(exc)[:200],
                extra={"engine": self.engine_name},
            )
            return None

    # -----------------------------------------------------------------
    # Peer delegation
    # -----------------------------------------------------------------

    async def _delegate(
        self,
        parent_request: MeshRequest,
        recipient_capability: str,
        payload: dict[str, Any],
    ) -> MeshResponse:
        """Delegate to a peer engine capability through the mesh router.

        Propagates task_id, trace_id, context_ref, and decrements delegation depth.

        Raises RuntimeError if no mesh router is configured.
        """
        if self._mesh_router is None:
            raise RuntimeError(
                f"{self.engine_name}: Cannot delegate — no mesh router configured."
            )

        peer_request = self._mesh_router.create_peer_request(
            parent_request=parent_request,
            sender_engine=self.engine_name,
            recipient_capability=recipient_capability,
            payload=payload,
        )
        return await self._mesh_router.dispatch(peer_request)

    # -----------------------------------------------------------------
    # Response factories
    # -----------------------------------------------------------------

    def _success(
        self,
        request: MeshRequest,
        payload: dict[str, Any],
        *,
        context_ref: Optional[str] = None,
    ) -> MeshResponse:
        """Build a success MeshResponse for this engine."""
        return MeshResponse.success(
            request=request,
            sender_engine=self.engine_name,
            payload=payload,
            context_ref=context_ref,
        )

    def _error(
        self,
        request: MeshRequest,
        status: ResultStatus,
        code: EngineErrorCode,
        message: str,
        *,
        details: Optional[dict[str, Any]] = None,
    ) -> MeshResponse:
        """Build a typed error MeshResponse for this engine."""
        return MeshResponse.failure(
            request=request,
            sender_engine=self.engine_name,
            status=status,
            errors=[
                MeshError(
                    code=code.value,
                    message=message,
                    engine=self.engine_name,
                    details=details,
                )
            ],
        )
