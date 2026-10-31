"""Domain-Blind Runtime Dispatcher for General Brain Capabilities.

Strictly non-orchestrating, domain-blind runtime capability dispatcher.
Validates capability registrations and permitted handoffs, executing steps
without embedded business or domain logic.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from brain.general.contracts.capabilities import CapabilityRegistry
from brain.general.contracts.context import BrainContext
from brain.general.contracts.protocols import EngineResult
from brain.general.policies.handoff import HandoffPolicy

logger = logging.getLogger("brain.general.dispatcher")


class DispatcherError(Exception):
    """Base exception for runtime dispatch errors."""

    def __init__(self, message: str, code: str, detail: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.detail = detail or {}


class RuntimeDispatcher:
    """Domain-blind capability router and handoff validator.
    
    Contains NO business logic. Acts strictly as a transport and validation
    dispatcher between peer capabilities.
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
        handoff_policy: Optional[HandoffPolicy] = None,
    ) -> None:
        self._registry = registry
        self._handoff_policy = handoff_policy or HandoffPolicy()

    async def dispatch(
        self,
        target_capability: str,
        payload: dict[str, Any],
        context: BrainContext,
        source_capability: Optional[str] = None,
        traversal_history: Optional[list[str]] = None,
    ) -> EngineResult:
        """Validate and dispatch a capability execution."""
        # 1. Validate Context
        if not context or not context.organization_id:
            logger.error("Dispatch rejected: missing or invalid BrainContext")
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )

        # 2. Validate Handoff Transition
        history = list(traversal_history) if traversal_history else []
        validation = self._handoff_policy.validate_handoff(
            source_capability=source_capability,
            target_capability=target_capability,
            traversal_history=history,
        )

        if not validation.is_permitted:
            logger.warning(
                "Dispatch rejected: disallowed handoff %s -> %s: %s",
                source_capability,
                target_capability,
                validation.detail,
            )
            return EngineResult(
                error={
                    "code": validation.reason.value if validation.reason else "DISALLOWED_HANDOFF",
                    "message": validation.detail,
                }
            )

        # 3. Lookup Handler in Registry
        handler = self._registry.lookup(target_capability)
        if handler is None:
            logger.error("Dispatch failed: capability '%s' not registered", target_capability)
            return EngineResult(
                error={
                    "code": "CAPABILITY_NOT_FOUND",
                    "message": f"Capability '{target_capability}' is not registered in runtime",
                }
            )

        # 4. Execute Handler
        try:
            result = await handler(payload, context)
            if isinstance(result, EngineResult):
                return result
            elif isinstance(result, dict):
                return EngineResult(data=result)
            else:
                return EngineResult(data={"result": result})
        except Exception as e:
            logger.exception("Error during capability execution '%s': %s", target_capability, str(e))
            return EngineResult(
                error={
                    "code": "EXECUTION_ERROR",
                    "message": str(e),
                }
            )
