"""Base engine class implementing the Intelligence Layer + Deterministic Core pattern.

Every General Brain engine inherits from BaseEngine. The base class provides:
- Capability registration with the mesh registry.
- Request validation (protocol version, context ref, constraints).
- Safe error wrapping so engines never leak raw stack traces.
- Provider-agnostic LLM integration via ILLMClient.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from brain.general.contracts.capabilities import CapabilityRegistry
from brain.general.contracts.envelopes import (
    PROTOCOL_VERSION,
    MeshError,
    MeshRequest,
    MeshResponse,
    ResultStatus,
)
from brain.general.contracts.errors import EngineErrorCode
from brain.general.contracts.llm import (
    ILLMClient,
    LLMMessage,
    LLMRequest,
    LLMRole,
)
from brain.general.runtime.router import MeshRouter


class BaseEngine(ABC):
    """Abstract base for all General Brain engines.

    Subclasses must implement:
    - engine_name: property returning the engine identifier
    - register_capabilities(registry): register handlers with the capability registry
    """

    def __init__(
        self,
        llm_client: Optional[ILLMClient] = None,
        mesh_router: Optional[MeshRouter] = None,
        llm_service: Optional[ILLMClient] = None,
        **kwargs: Any,
    ) -> None:
        self._llm_client = llm_client if llm_client is not None else llm_service
        self._mesh_router = mesh_router
        self._logger = logging.getLogger(f"brain.general.{self.engine_name}")

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Unique identifier for this engine (e.g. 'perception', 'observation')."""
        ...

    @abstractmethod
    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        """Register capability handlers with the registry."""
        ...

    # -----------------------------------------------------------------
    # Validation helpers
    # -----------------------------------------------------------------

    def validate_request(self, request: MeshRequest) -> Optional[MeshResponse]:
        """Validate protocol version and basic request sanity.

        Returns None if valid; returns a failure MeshResponse if invalid.
        """
        if request.protocol_version != PROTOCOL_VERSION:
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.UNSUPPORTED_PROTOCOL_VERSION,
                f"Protocol version '{request.protocol_version}' not supported.",
            )

        if not request.recipient_capability:
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.INVALID_PAYLOAD,
                "Recipient capability is required.",
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
    # Intelligence Layer: Provider-Agnostic LLM interaction
    # -----------------------------------------------------------------

    async def _call_llm(
        self,
        system_prompt: str,
        user_content: str,
        *,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 2000,
        model_hint: Optional[str] = None,
    ) -> Optional[str]:
        """Call the LLM via the injected ILLMClient.

        Returns the response content string, or None if the LLM is unavailable
        or returns an error. Never raises — errors are logged and None is returned
        for the caller to handle with a deterministic fallback.
        """
        if self._llm_client is None:
            self._logger.debug("LLM client not configured; using deterministic fallback.")
            return None

        try:
            if hasattr(self._llm_client, "complete"):
                req = LLMRequest(
                    messages=(
                        LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                        LLMMessage(role=LLMRole.USER, content=user_content),
                    ),
                    model_hint=model_hint,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                resp = await self._llm_client.complete(req)
                return resp.content
            elif hasattr(self._llm_client, "generate"):
                import sys
                ai_req_mod = sys.modules.get("ai.core.types.request")
                if ai_req_mod is not None:
                    b_req = ai_req_mod.LLMRequest(
                        messages=[
                            ai_req_mod.LLMMessage(role="system", content=system_prompt),
                            ai_req_mod.LLMMessage(role="user", content=user_content),
                        ],
                        model=model_hint or "gpt-4o-mini",
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                else:
                    class _SimpleMsg:
                        def __init__(self, role: str, content: str) -> None:
                            self.role = role
                            self.content = content
                    class _SimpleReq:
                        def __init__(self, messages: list, model: str, temperature: float, max_tokens: Optional[int]) -> None:
                            self.messages = messages
                            self.model = model
                            self.temperature = temperature
                            self.max_tokens = max_tokens
                    b_req = _SimpleReq(
                        messages=[
                            _SimpleMsg("system", system_prompt),
                            _SimpleMsg("user", user_content),
                        ],
                        model=model_hint or "gpt-4o-mini",
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                resp = await self._llm_client.generate(b_req)
                return getattr(resp, "content", None) or str(resp)
            else:
                self._logger.warning("Unknown LLM client interface on '%s'", self.engine_name)
                return None
        except Exception as exc:
            self._logger.warning(
                "LLM call failed in engine '%s': %s",
                self.engine_name,
                str(exc),
            )
            return None

    async def _call_llm_json(
        self,
        system_prompt: str,
        user_content: str,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """Call the LLM and attempt to parse the response as JSON."""
        raw = await self._call_llm(system_prompt, user_content, **kwargs)
        if raw is None:
            return None

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            return {"result": parsed}
        except json.JSONDecodeError:
            self._logger.warning("LLM response was not valid JSON: %s", raw[:200])
            return None

    # -----------------------------------------------------------------
    # Delegation helper
    # -----------------------------------------------------------------

    async def _delegate(
        self,
        parent_request: MeshRequest,
        recipient_capability: str,
        payload: dict[str, Any],
    ) -> MeshResponse:
        """Send a sub-request to a peer capability via the mesh router."""
        if self._mesh_router is None:
            return self._error(
                parent_request,
                ResultStatus.FAILED,
                EngineErrorCode.INTERNAL_ERROR,
                "Cannot delegate: MeshRouter is not configured on this engine.",
            )

        child_req = self._mesh_router.create_peer_request(
            parent_request=parent_request,
            sender_engine=self.engine_name,
            recipient_capability=recipient_capability,
            payload=payload,
        )
        return await self._mesh_router.dispatch(child_req)

    # -----------------------------------------------------------------
    # Response builder helpers
    # -----------------------------------------------------------------

    def _success(
        self,
        request: MeshRequest,
        payload: dict[str, Any],
        *,
        context_ref: Any = None,
        plan_version: Optional[int] = None,
    ) -> MeshResponse:
        return MeshResponse.success(
            request,
            self.engine_name,
            payload,
            context_ref=context_ref,
            plan_version=plan_version,
        )

    def _error(
        self,
        request: MeshRequest,
        status: ResultStatus,
        code: EngineErrorCode,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> MeshResponse:
        return MeshResponse.failure(
            request,
            self.engine_name,
            status,
            [
                MeshError(
                    code=code.value,
                    message=message,
                    engine=self.engine_name,
                    details=details,
                )
            ],
        )
