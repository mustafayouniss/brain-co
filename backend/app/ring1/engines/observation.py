"""Observation Engine — background event capture and observation service.

Deterministic Core:
- Capture and normalize events
- Record observations with metadata and trace info
- Duplicate detection via idempotency key
- Explicit event policies for record-only vs follow-up

Intelligence Layer:
- Determine whether an unfamiliar event requires follow-up (when no explicit rule exists)

Must not: become the central orchestrator, start arbitrary workflows,
treat raw observations as trusted knowledge, bypass context/authorization.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.ring1.contracts.capabilities import (
    OBSERVATION_RECORD_EVENT,
    PLANNING_CREATE_PLAN,
    CapabilityRegistry,
)
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.base import BaseEngine
from app.ring1.models.observation import Observation


# Default event types that are record-only (no follow-up)
_RECORD_ONLY_EVENT_TYPES: frozenset[str] = frozenset({
    "heartbeat",
    "metric",
    "log_entry",
    "status_check",
    "audit_entry",
})

# Event types that explicitly trigger follow-up work
_FOLLOW_UP_EVENT_TYPES: frozenset[str] = frozenset({
    "document.uploaded",
    "case.created",
    "message.received",
    "task.requested",
})


class ObservationEngine(BaseEngine):
    """Ring 1 Observation Engine [GB].

    Records system events, user actions, and external triggers as normalized
    observations. Determines whether each event is record-only or eligible
    for follow-up through explicit event policies.
    """

    def __init__(self, db_session_factory=None, **kwargs):
        """Initialize with an optional database session factory.

        Args:
            db_session_factory: Callable returning a SQLAlchemy Session.
                When provided, observations are persisted to the database.
                When None, observations are recorded in-memory (for testing
                or when DB is not yet available).
        """
        super().__init__(**kwargs)
        self._db_session_factory = db_session_factory
        self._in_memory_observations: list[dict[str, Any]] = []

    @property
    def engine_name(self) -> str:
        return "observation"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        registry.register(
            OBSERVATION_RECORD_EVENT,
            self.engine_name,
            self.handle_record_event,
            description="Capture, normalize, and persist an event observation.",
        )

    # -----------------------------------------------------------------
    # Capability handler
    # -----------------------------------------------------------------

    async def handle_record_event(self, request: MeshRequest) -> MeshResponse:
        """Record an event as a normalized observation.

        Decision order:
        1. Validate request
        2. Normalize event payload
        3. Check for duplicates (idempotency)
        4. Persist the observation
        5. Determine if follow-up is needed
        6. Return typed result with observation ID and follow-up status
        """
        # Step 1: Validate
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        payload = request.payload
        event_id = payload.get("event_id") or f"evt-{uuid.uuid4().hex[:12]}"
        event_type = payload.get("event_type", "")

        if not event_type:
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.INVALID_PAYLOAD,
                "'event_type' is required in the payload.",
            )

        # Step 2: Normalize
        normalized = self._normalize_event(payload, event_id)

        # Step 3: Duplicate check
        idempotency_key = payload.get("idempotency_key") or event_id
        duplicate = await self._check_duplicate(idempotency_key, request)
        if duplicate is not None:
            return duplicate

        # Step 4: Persist
        observation_id = await self._persist_observation(
            normalized, request, idempotency_key
        )

        # Step 5: Determine follow-up
        if "requires_follow_up" in payload:
            requires_follow_up = bool(payload["requires_follow_up"])
        elif "follow_up_required" in payload:
            requires_follow_up = bool(payload["follow_up_required"])
        else:
            requires_follow_up = self._should_follow_up(event_type)

        # Step 6: Genuine Peer Delegation (if follow-up required and router is configured)
        delegated_result = None
        if (
            requires_follow_up
            and self._mesh_router is not None
            and request.constraints.max_delegations_remaining > 0
            and payload.get("auto_delegate", True)
        ):
            target_cap = payload.get("follow_up_capability") or PLANNING_CREATE_PLAN
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
                delegated_result = {
                    "capability": target_cap,
                    "status": "error",
                    "error": str(exc),
                }

        # Step 7: Return typed result
        result_payload = {
            "observation_id": observation_id,
            "event_id": event_id,
            "event_type": event_type,
            "source": normalized.get("source", "unknown"),
            "timestamp": normalized["timestamp"],
            "context_ref": request.context_ref,
            "status": "recorded",
            "duplicate": False,
            "trace_id": request.trace_id,
            "requires_follow_up": requires_follow_up,
            "follow_up_required": requires_follow_up,
            "follow_up_capability": PLANNING_CREATE_PLAN if requires_follow_up else None,
        }
        if delegated_result is not None:
            result_payload["delegated_result"] = delegated_result

        return self._success(request, result_payload)


    # -----------------------------------------------------------------
    # Deterministic core
    # -----------------------------------------------------------------

    @staticmethod
    def _normalize_event(
        payload: dict[str, Any], event_id: str
    ) -> dict[str, Any]:
        """Normalize an event payload into a standard structure."""
        return {
            "event_id": event_id,
            "event_type": payload.get("event_type", "unknown"),
            "source": payload.get("source", "unknown"),
            "timestamp": payload.get(
                "timestamp",
                datetime.now(timezone.utc).isoformat(),
            ),
            "actor_ref": payload.get("actor_ref"),
            "payload": payload.get("payload", {}),
            "metadata": payload.get("metadata", {}),
        }

    async def _check_duplicate(
        self,
        idempotency_key: str,
        request: MeshRequest,
    ) -> Optional[MeshResponse]:
        """Check for duplicate observations using the idempotency key.

        Returns a duplicate-status response if found, None otherwise.
        """
        if self._db_session_factory:
            session: Session = self._db_session_factory()
            try:
                existing = (
                    session.query(Observation)
                    .filter(Observation.idempotency_key == idempotency_key)
                    .first()
                )
                if existing:
                    return self._success(request, {
                        "observation_id": str(existing.id),
                        "event_id": existing.event_id,
                        "event_type": existing.event_type,
                        "status": "duplicate",
                        "duplicate": True,
                        "trace_id": request.trace_id,
                        "requires_follow_up": False,
                        "follow_up_required": False,
                    })
            finally:
                session.close()
        else:
            # In-memory duplicate check
            for obs in self._in_memory_observations:
                if obs.get("idempotency_key") == idempotency_key:
                    return self._success(request, {
                        "observation_id": obs.get("observation_id", ""),
                        "event_id": obs.get("event_id", ""),
                        "event_type": obs.get("event_type", ""),
                        "status": "duplicate",
                        "duplicate": True,
                        "trace_id": request.trace_id,
                        "requires_follow_up": False,
                        "follow_up_required": False,
                    })
        return None


    async def _persist_observation(
        self,
        normalized: dict[str, Any],
        request: MeshRequest,
        idempotency_key: str,
    ) -> str:
        """Persist the observation to the database or in-memory store."""
        observation_id = str(uuid.uuid4())
        ctx_ref_str = (
            request.context_ref.ref
            if hasattr(request.context_ref, "ref")
            else str(request.context_ref)
            if request.context_ref
            else None
        )
        ctx = request.context_ref
        case_id = (
            getattr(ctx, "case_id", None)
            if ctx is not None
            else request.payload.get("case_id")
        )
        organization_id = (
            getattr(ctx, "organization_id", None)
            if ctx is not None
            else request.payload.get("organization_id")
        )

        if self._db_session_factory:
            session: Session = self._db_session_factory()
            try:
                obs = Observation(
                    event_id=normalized["event_id"],
                    event_type=normalized["event_type"],
                    source=normalized["source"],
                    actor_ref=normalized.get("actor_ref"),
                    context_ref=ctx_ref_str,
                    case_id=case_id,
                    organization_id=organization_id,
                    payload=normalized.get("payload"),
                    metadata_=normalized.get("metadata"),
                    trace_id=request.trace_id,
                    task_id=request.task_id,
                    idempotency_key=idempotency_key,
                    event_timestamp=datetime.fromisoformat(normalized["timestamp"])
                    if normalized.get("timestamp")
                    else None,
                )
                session.add(obs)
                session.commit()
                observation_id = str(obs.id)
            except Exception as exc:
                session.rollback()
                self._logger.error("Failed to persist observation: %s", str(exc))
                raise

            finally:
                session.close()
        else:
            self._in_memory_observations.append({
                "observation_id": observation_id,
                "idempotency_key": idempotency_key,
                **normalized,
            })

        return observation_id

    @staticmethod
    def _should_follow_up(event_type: str) -> bool:
        """Determine whether an event requires follow-up work.

        Uses explicit event type policies:
        - Record-only types → no follow-up
        - Follow-up types → trigger planning
        - Unknown types → record only (safe default)
        """
        if event_type in _RECORD_ONLY_EVENT_TYPES:
            return False
        if event_type in _FOLLOW_UP_EVENT_TYPES:
            return True
        # Unknown event types default to record-only (safe)
        return False
