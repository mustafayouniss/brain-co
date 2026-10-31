"""Mesh router: capability dispatch, validation, tracing, and delegation control.

The router is NOT a central orchestrator. It is a shared infrastructure service
that engines use to send validated requests to peer capabilities. Each engine
still owns and executes its own capabilities.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from brain.general.contracts.capabilities import CapabilityRegistry
from brain.general.contracts.envelopes import (
    PROTOCOL_VERSION,
    MeshConstraints,
    MeshError,
    MeshRequest,
    MeshResponse,
    MessageType,
    ResultStatus,
)
from brain.general.contracts.errors import EngineErrorCode

logger = logging.getLogger("brain.general.mesh")


class MeshRouter:
    """In-process peer-to-peer mesh router for General Brain engines."""

    def __init__(
        self,
        registry: CapabilityRegistry,
        default_timeout_seconds: float = 30.0,
    ) -> None:
        self._registry = registry
        self._default_timeout_seconds = default_timeout_seconds

    async def dispatch(self, request: MeshRequest) -> MeshResponse:
        """Validate and dispatch a mesh request to the target capability handler."""
        start = time.monotonic()

        # 1. Protocol version
        if request.protocol_version != PROTOCOL_VERSION:
            return self._error_response(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.UNSUPPORTED_PROTOCOL_VERSION,
                f"Unsupported protocol version '{request.protocol_version}'. "
                f"Expected '{PROTOCOL_VERSION}'.",
            )

        # 2. Capability lookup
        handler = self._registry.lookup(request.recipient_capability)
        if handler is None:
            return self._error_response(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.CAPABILITY_NOT_FOUND,
                f"Unknown capability '{request.recipient_capability}'. "
                f"Registered: {self._registry.list_capabilities()}",
            )

        # 3. Delegation depth
        if request.constraints.max_delegations_remaining <= 0:
            return self._error_response(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.DELEGATION_DEPTH_EXCEEDED,
                "Maximum delegation depth exceeded. Potential loop detected.",
            )

        # 4. Execute with timeout
        timeout = request.constraints.timeout_seconds
        try:
            response: MeshResponse = await asyncio.wait_for(
                handler(request),
                timeout=timeout,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "mesh.dispatch completed",
                extra={
                    "task_id": request.task_id,
                    "trace_id": request.trace_id,
                    "capability": request.recipient_capability,
                    "status": response.status.value,
                    "elapsed_ms": elapsed_ms,
                },
            )
            return response

        except asyncio.TimeoutError:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.warning(
                "mesh.dispatch timeout",
                extra={
                    "task_id": request.task_id,
                    "trace_id": request.trace_id,
                    "capability": request.recipient_capability,
                    "timeout_seconds": timeout,
                    "elapsed_ms": elapsed_ms,
                },
            )
            return self._error_response(
                request,
                ResultStatus.TIMEOUT,
                EngineErrorCode.PEER_TIMEOUT,
                f"Capability '{request.recipient_capability}' timed out after {timeout}s.",
            )

        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "mesh.dispatch error",
                extra={
                    "task_id": request.task_id,
                    "trace_id": request.trace_id,
                    "capability": request.recipient_capability,
                    "error": str(exc),
                    "elapsed_ms": elapsed_ms,
                },
                exc_info=False,
            )
            return self._error_response(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.PEER_FAILURE,
                f"Capability '{request.recipient_capability}' raised an error: {type(exc).__name__}",
            )

    def create_peer_request(
        self,
        parent_request: MeshRequest,
        sender_engine: str,
        recipient_capability: str,
        payload: dict,
        *,
        message_type: MessageType = MessageType.CAPABILITY_REQUEST,
    ) -> MeshRequest:
        """Create a child request that inherits traceability from a parent."""
        return MeshRequest(
            task_id=parent_request.task_id,
            trace_id=parent_request.trace_id,
            parent_message_id=parent_request.message_id,
            sender_engine=sender_engine,
            recipient_capability=recipient_capability,
            message_type=message_type,
            plan_version=parent_request.plan_version,
            context_ref=parent_request.context_ref,
            deadline=parent_request.deadline,
            payload=payload,
            constraints=MeshConstraints(
                max_delegations_remaining=parent_request.constraints.max_delegations_remaining - 1,
                max_retries=parent_request.constraints.max_retries,
                timeout_seconds=parent_request.constraints.timeout_seconds,
                idempotency_key=None,
            ),
        )

    @staticmethod
    def _error_response(
        request: MeshRequest,
        status: ResultStatus,
        code: EngineErrorCode,
        message: str,
    ) -> MeshResponse:
        """Build a standardized error MeshResponse."""
        return MeshResponse.failure(
            request=request,
            sender_engine="mesh_router",
            status=status,
            errors=[
                MeshError(
                    code=code.value,
                    message=message,
                    engine="mesh_router",
                )
            ],
        )
