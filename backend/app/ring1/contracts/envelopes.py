"""Typed mesh request and response envelopes for Ring 1 inter-engine communication.

All peer-to-peer messages flow through these versioned envelopes. They carry
task identity, traceability metadata, context references, and delegation
constraints so that every hop is validated and bounded.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from app.ring1.contracts.context_ref import ContextRef


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROTOCOL_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MessageType(str, Enum):
    """Discriminator for mesh message purpose."""

    CAPABILITY_REQUEST = "capability_request"
    CAPABILITY_RESULT = "capability_result"
    REPLAN_REQUEST = "replan_request"
    REPLAN_RESULT = "replan_result"


class ResultStatus(str, Enum):
    """Outcome status carried in every mesh response."""

    SUCCESS = "success"
    PARTIAL = "partial"
    NEEDS_CLARIFICATION = "needs_clarification"
    REPLAN_REQUIRED = "replan_required"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    UNAUTHORIZED = "unauthorized"
    INVALID_REQUEST = "invalid_request"
    TIMEOUT = "timeout"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------

class MeshConstraints(BaseModel):
    """Delegation-depth, retry, and timeout limits propagated with requests."""

    model_config = ConfigDict(frozen=True)

    max_delegations_remaining: int = Field(default=10, ge=0)
    max_retries: int = Field(default=3, ge=0)
    timeout_seconds: float = Field(default=30.0, gt=0)
    idempotency_key: Optional[str] = None


# Alias for explicit delegation constraints terminology
DelegationConstraints = MeshConstraints


# ---------------------------------------------------------------------------
# Error detail
# ---------------------------------------------------------------------------

class MeshError(BaseModel):
    """Structured error payload returned in mesh responses."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    engine: Optional[str] = None
    details: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Request envelope
# ---------------------------------------------------------------------------

def _new_msg_id() -> str:
    return f"msg-{uuid.uuid4().hex[:12]}"


class MeshRequest(BaseModel):
    """Typed, versioned request envelope for peer-to-peer engine communication.

    Every field has a clear purpose:
    - Identification: message_id, task_id, trace_id
    - Routing: sender_engine, recipient_capability
    - Traceability: parent_message_id, plan_version
    - Security: context_ref
    - Payload: payload, constraints
    """

    model_config = ConfigDict(extra="forbid")

    protocol_version: str = Field(default=PROTOCOL_VERSION)
    message_id: str = Field(default_factory=_new_msg_id)
    task_id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:12]}")
    trace_id: str = Field(default_factory=lambda: f"trace-{uuid.uuid4().hex[:12]}")
    parent_message_id: Optional[str] = None
    sender_engine: str
    recipient_capability: str
    message_type: MessageType = MessageType.CAPABILITY_REQUEST
    plan_version: Optional[int] = None
    context_ref: Optional[Union[ContextRef, str]] = None
    deadline: Optional[datetime] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    constraints: MeshConstraints = Field(default_factory=MeshConstraints)


# ---------------------------------------------------------------------------
# Response envelope
# ---------------------------------------------------------------------------

class MeshResponse(BaseModel):
    """Typed, versioned response envelope returned from capability execution.

    Carries correlation identifiers, status, structured payload or error, and
    the context reference for downstream consumers.
    """

    model_config = ConfigDict(extra="forbid")

    protocol_version: str = Field(default=PROTOCOL_VERSION)
    message_id: str = Field(default_factory=_new_msg_id)
    in_reply_to: str
    task_id: str
    trace_id: str
    sender_engine: str
    message_type: MessageType = MessageType.CAPABILITY_RESULT
    status: ResultStatus
    payload: dict[str, Any] = Field(default_factory=dict)
    errors: list[MeshError] = Field(default_factory=list)
    context_ref: Optional[str] = None
    plan_version: Optional[int] = None

    @property
    def correlation_id(self) -> str:
        """Alias for in_reply_to."""
        return self.in_reply_to

    @classmethod
    def success(
        cls,
        request: MeshRequest,
        sender_engine: str,
        payload: dict[str, Any],
        *,
        context_ref: Optional[Union[ContextRef, str]] = None,
        plan_version: Optional[int] = None,
    ) -> MeshResponse:
        """Convenience factory for a successful response."""
        resolved_ctx = context_ref or request.context_ref
        ctx_str = (
            resolved_ctx.ref
            if isinstance(resolved_ctx, ContextRef)
            else str(resolved_ctx)
            if resolved_ctx is not None
            else None
        )
        return cls(
            in_reply_to=request.message_id,
            task_id=request.task_id,
            trace_id=request.trace_id,
            sender_engine=sender_engine,
            status=ResultStatus.SUCCESS,
            payload=payload,
            context_ref=ctx_str,
            plan_version=plan_version or request.plan_version,
        )

    @classmethod
    def failure(
        cls,
        request: MeshRequest,
        sender_engine: str,
        status: ResultStatus,
        errors: list[MeshError],
        *,
        context_ref: Optional[Union[ContextRef, str]] = None,
    ) -> MeshResponse:
        """Convenience factory for a failure response."""
        resolved_ctx = context_ref or request.context_ref
        ctx_str = (
            resolved_ctx.ref
            if isinstance(resolved_ctx, ContextRef)
            else str(resolved_ctx)
            if resolved_ctx is not None
            else None
        )
        return cls(
            in_reply_to=request.message_id,
            task_id=request.task_id,
            trace_id=request.trace_id,
            sender_engine=sender_engine,
            status=status,
            errors=errors,
            context_ref=ctx_str,
        )
