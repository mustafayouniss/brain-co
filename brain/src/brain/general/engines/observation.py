"""Observation Engine — background event capture and observation service.

Deterministic Core:
- Capture and normalize events
- Record observations with metadata and trace info
- Duplicate detection via idempotency key
- Explicit event policies for record-only vs follow-up
- Query feed via injected IObservationStore

Intelligence Layer:
- Determine whether an unfamiliar event requires follow-up (when no explicit rule exists)

Must not: become the central orchestrator, start arbitrary workflows,
autonomously trigger PlanningEngine, treat raw observations as trusted knowledge,
bypass context/authorization, or depend directly on database infrastructure.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from brain.general.contracts.capabilities import (
    OBSERVATION_RECORD_EVENT,
    CapabilityRegistry,
)
from brain.general.contracts.context import BrainContext
from brain.general.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from brain.general.contracts.errors import EngineErrorCode, StorageConfigurationError
from brain.general.contracts.llm import ILLMClient
from brain.general.contracts.protocols import (
    EngineResult,
    IObservationEngine,
    ObservationFeedResult,
)
from brain.general.contracts.storage import IObservationStore
from brain.general.engines.base import BaseEngine
from brain.general.runtime.router import MeshRouter

# Default event types that are record-only (no follow-up)
_RECORD_ONLY_EVENT_TYPES: frozenset[str] = frozenset({
    "heartbeat",
    "metric",
    "log_entry",
    "status_check",
    "audit_entry",
})

# Event types that explicitly indicate follow-up work is eligible
_FOLLOW_UP_EVENT_TYPES: set[str] = {
    "document.uploaded",
    "case.created",
    "entity.created",
    "message.received",
    "task.requested",
}


class ObservationEngine(BaseEngine, IObservationEngine):
    """General Brain Observation Engine [GB].

    Captures, normalizes, and records observations. Requires an explicit
    IObservationStore implementation injected at initialization.
    """

    def __init__(
        self,
        store: Optional[IObservationStore] = None,
        llm_client: Optional[ILLMClient] = None,
        mesh_router: Optional[MeshRouter] = None,
        llm_service: Optional[ILLMClient] = None,
        **kwargs: Any,
    ) -> None:
        if store is None:
            raise StorageConfigurationError(
                "ObservationEngine requires an explicit IObservationStore implementation. "
                "For test or CLI use, inject InMemoryObservationStore(). "
                "For production, inject a database store adapter."
            )
        super().__init__(
            llm_client=llm_client,
            mesh_router=mesh_router,
            llm_service=llm_service,
            **kwargs,
        )
        self._store = store

    @property
    def store(self) -> IObservationStore:
        return self._store

    @property
    def _in_memory_observations(self) -> list[dict[str, Any]]:
        if hasattr(self._store, "observations"):
            return self._store.observations
        return []

    @property
    def engine_name(self) -> str:
        return "observation"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        registry.register(
            OBSERVATION_RECORD_EVENT,
            self.engine_name,
            self.handle_record_event,
            description="Capture, normalize, and record an event as an observation.",
        )

    # -----------------------------------------------------------------
    # Pure Engine Protocol implementation (Decoupled from Transport)
    # -----------------------------------------------------------------

    async def record_observation(
        self,
        observation_data: dict[str, Any],
        context: BrainContext,
    ) -> EngineResult:
        """Transport-independent recording of an observation event."""
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )

        event_type = observation_data.get("event_type", "")
        if not event_type:
            return EngineResult(
                error={"code": EngineErrorCode.INVALID_PAYLOAD.value, "message": "'event_type' is required."}
            )

        event_id = observation_data.get("event_id") or f"evt-{uuid.uuid4().hex[:12]}"
        idempotency_key = observation_data.get("idempotency_key") or event_id

        # 1. Duplicate check via store
        existing = await self._store.find_by_idempotency_key(idempotency_key)
        if existing:
            return EngineResult(
                data={
                    "observation_id": str(existing.get("id") or existing.get("observation_id")),
                    "event_id": existing.get("event_id"),
                    "event_type": existing.get("event_type"),
                    "status": "duplicate",
                    "duplicate": True,
                    "requires_follow_up": False,
                }
            )

        # 2. Normalize
        normalized = self._normalize_event(observation_data, event_id)

        # 3. Persist via store
        to_save = {
            "event_id": normalized["event_id"],
            "event_type": normalized["event_type"],
            "source": normalized["source"],
            "actor_ref": normalized.get("actor_ref") or context.user_id,
            "case_id": context.effective_scope_id,
            "scope_id": context.effective_scope_id,
            "organization_id": context.organization_id,
            "payload": normalized.get("payload"),
            "metadata": normalized.get("metadata"),
            "trace_id": context.correlation_id,
            "task_id": context.task_id,
            "idempotency_key": idempotency_key,
            "timestamp": normalized.get("timestamp"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        observation_id = await self._store.save(to_save)

        # 4. Determine follow-up
        if "requires_follow_up" in observation_data:
            requires_follow_up = bool(observation_data["requires_follow_up"])
        elif "follow_up_required" in observation_data:
            requires_follow_up = bool(observation_data["follow_up_required"])
        else:
            requires_follow_up = await self._should_follow_up(event_type)

        data = {
            "observation_id": observation_id,
            "event_id": event_id,
            "event_type": event_type,
            "status": "recorded",
            "duplicate": False,
            "requires_follow_up": requires_follow_up,
            "follow_up_required": requires_follow_up,
            "metadata": normalized.get("metadata", {}),
        }

        # Observation does NOT autonomously propose planning (governed by HandoffPolicy)
        return EngineResult(data=data)

    async def list_observations(
        self,
        context: BrainContext,
        cursor: Optional[str] = None,
        limit: int = 50,
        filters: Optional[dict[str, Any]] = None,
    ) -> ObservationFeedResult:
        """Query observation feed bounded by scope and keyset pagination."""
        if not context or not context.organization_id:
            return ObservationFeedResult(items=[], next_cursor=None, has_more=False, total_count=0)

        f = filters or {}
        event_type = f.get("event_type") or f.get("type")
        source = f.get("source")

        # Parse cursor if string formatted as created_at:id
        cursor_created_at = None
        cursor_id = None
        if cursor and ":" in cursor:
            parts = cursor.split(":", 1)
            cursor_created_at = parts[0]
            cursor_id = parts[1]

        return await self._store.list_feed(
            organization_id=context.organization_id,
            case_id=context.effective_scope_id,
            event_type=event_type,
            source=source,
            limit=limit,
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
        )

    # -----------------------------------------------------------------
    # Capability handler (Mesh Adapter for Backward Compatibility)
    # -----------------------------------------------------------------

    async def handle_record_event(self, request: MeshRequest) -> MeshResponse:
        """Record an event as a normalized observation via mesh adapter."""
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        payload = request.payload
        event_type = payload.get("event_type", "")
        if not event_type:
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.INVALID_PAYLOAD,
                "'event_type' is required in the payload.",
            )

        event_id = payload.get("event_id") or f"evt-{uuid.uuid4().hex[:12]}"
        idempotency_key = payload.get("idempotency_key") or event_id

        # Duplicate check
        existing = await self._store.find_by_idempotency_key(idempotency_key)
        if existing:
            return self._success(request, {
                "observation_id": str(existing.get("id") or existing.get("observation_id")),
                "event_id": existing.get("event_id"),
                "event_type": existing.get("event_type"),
                "status": "duplicate",
                "duplicate": True,
                "trace_id": request.trace_id,
                "requires_follow_up": False,
                "follow_up_required": False,
            })

        normalized = self._normalize_event(payload, event_id)
        ctx = request.context_ref
        case_id = getattr(ctx, "case_id", None) if ctx else payload.get("case_id")
        org_id = getattr(ctx, "organization_id", None) if ctx else payload.get("organization_id")

        to_save = {
            "event_id": normalized["event_id"],
            "event_type": normalized["event_type"],
            "source": normalized["source"],
            "actor_ref": normalized.get("actor_ref"),
            "case_id": case_id,
            "scope_id": case_id,
            "organization_id": org_id or "org-default",
            "payload": normalized.get("payload"),
            "metadata": normalized.get("metadata"),
            "trace_id": request.trace_id,
            "task_id": request.task_id,
            "idempotency_key": idempotency_key,
            "timestamp": normalized.get("timestamp"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        observation_id = await self._store.save(to_save)

        # Determine follow-up
        if "requires_follow_up" in payload:
            requires_follow_up = bool(payload["requires_follow_up"])
        elif "follow_up_required" in payload:
            requires_follow_up = bool(payload["follow_up_required"])
        else:
            requires_follow_up = await self._should_follow_up(event_type)

        delegated_result = None
        if (
            requires_follow_up
            and self._mesh_router is not None
            and request.constraints.max_delegations_remaining > 0
            and payload.get("auto_delegate", True)
        ):
            target_cap = payload.get("follow_up_capability") or "planning.create_plan"
            delegated_payload = payload.get("follow_up_payload") or {
                "goal": f"Execute follow-up for observed event: {event_type}",
                "context": {
                    "observation_id": observation_id,
                    "event_type": event_type,
                    "source": normalized.get("source", "unknown"),
                },
            }
            try:
                delegated_resp = await self._delegate(
                    parent_request=request,
                    recipient_capability=target_cap,
                    payload=delegated_payload,
                )
                delegated_result = {
                    "capability": target_cap,
                    "status": delegated_resp.status.value,
                    "payload": delegated_resp.payload,
                    "errors": [e.model_dump() for e in delegated_resp.errors] if delegated_resp.errors else [],
                }
            except Exception as exc:
                self._logger.warning("Delegation from observation failed: %s", exc)

        response_payload = {
            "observation_id": observation_id,
            "event_id": event_id,
            "event_type": event_type,
            "status": "recorded",
            "duplicate": False,
            "trace_id": request.trace_id,
            "requires_follow_up": requires_follow_up,
            "follow_up_required": requires_follow_up,
            "metadata": normalized.get("metadata", {}),
        }
        if delegated_result is not None:
            response_payload["delegated_result"] = delegated_result

        return self._success(request, response_payload)

    # -----------------------------------------------------------------
    # Normalization & Helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _normalize_event(payload: dict[str, Any], event_id: str) -> dict[str, Any]:
        """Normalize an incoming event payload."""
        event_type = payload.get("event_type", "unknown")
        source = payload.get("source", "unknown")
        actor_ref = payload.get("actor_ref") or payload.get("actor_id")
        ts = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {"raw_metadata": metadata}

        body = payload.get("payload", {})
        if not isinstance(body, dict):
            body = {"value": body}

        return {
            "event_id": event_id,
            "event_type": event_type,
            "source": source,
            "actor_ref": actor_ref,
            "timestamp": ts,
            "metadata": metadata,
            "payload": body,
        }

    async def _should_follow_up(self, event_type: str) -> bool:
        """Deterministic policy + Intelligence Layer for follow-up eligibility."""
        if event_type in _RECORD_ONLY_EVENT_TYPES:
            return False
        if event_type in _FOLLOW_UP_EVENT_TYPES:
            return True

        # Intelligence Layer check if unfamiliar event
        if self._llm_client:
            prompt = (
                "You are the Observation Engine of Ring 1 General Brain. "
                "Determine if the following event type represents an actionable business event "
                "that warrants downstream follow-up (e.g. planning, context resolution, analysis). "
                "Heartbeats, metrics, telemetry, and simple status logs do NOT warrant follow-up. "
                "Return JSON: {'requires_follow_up': bool, 'reason': str}."
            )
            result = await self._call_llm_json(prompt, f"event_type: {event_type}")
            if result and isinstance(result, dict):
                return bool(result.get("requires_follow_up", False))

        return False
