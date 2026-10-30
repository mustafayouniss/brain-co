"""Observation Engine — background event capture and observation service.

Deterministic Core:
- Capture and normalize events
- Record observations with metadata and trace info
- Duplicate detection via idempotency key
- Explicit event policies for record-only vs follow-up
- Cursor-based feed pagination using HMAC-signed cursors

Intelligence Layer:
- Determine whether an unfamiliar event requires follow-up (when no explicit rule exists)

Must not: become the central orchestrator, start arbitrary workflows,
autonomously trigger PlanningEngine, treat raw observations as trusted knowledge,
bypass context/authorization.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.context import BrainContext
from app.core.cursor import decode_and_verify_cursor, encode_cursor
from app.ring1.contracts.capabilities import (
    OBSERVATION_RECORD_EVENT,
    CapabilityRegistry,
)
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.protocols import (
    EngineResult,
    IObservationEngine,
    ObservationFeedResult,
)
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

# Event types that explicitly indicate follow-up work is eligible
_FOLLOW_UP_EVENT_TYPES: frozenset[str] = frozenset({
    "document.uploaded",
    "case.created",
    "message.received",
    "task.requested",
})


class ObservationEngine(BaseEngine, IObservationEngine):
    """Ring 1 Observation Engine [GB].

    Records system events, user actions, and external triggers as normalized
    observations. Strictly non-orchestrating: records observations and exposes
    paginated cursor feeds without autonomously initiating planning workflows.
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
    # Pure Engine Protocol implementation (Decoupled from Transport)
    # -----------------------------------------------------------------

    async def record_observation(
        self,
        observation_data: dict[str, Any],
        context: BrainContext,
    ) -> EngineResult:
        """Transport-independent record observation method."""
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )

        payload = observation_data
        event_id = payload.get("event_id") or f"evt-{uuid.uuid4().hex[:12]}"
        event_type = payload.get("event_type", "")

        if not event_type:
            return EngineResult(
                error={"code": EngineErrorCode.INVALID_PAYLOAD.value, "message": "'event_type' is required."}
            )

        normalized = self._normalize_event(payload, event_id)
        idempotency_key = payload.get("idempotency_key") or event_id

        # Duplicate check
        duplicate_obs_id = await self._check_duplicate_id(idempotency_key)
        if duplicate_obs_id:
            return EngineResult(
                data={
                    "observation_id": duplicate_obs_id,
                    "event_id": event_id,
                    "event_type": event_type,
                    "status": "duplicate",
                    "duplicate": True,
                    "requires_follow_up": False,
                    "follow_up_required": False,
                }
            )

        # Persist observation with context boundaries
        obs_id = await self._persist_observation_data(
            normalized=normalized,
            context=context,
            idempotency_key=idempotency_key,
            trace_id=payload.get("trace_id"),
            task_id=payload.get("task_id"),
        )

        requires_follow_up = self._should_follow_up(event_type)
        if "requires_follow_up" in payload:
            requires_follow_up = bool(payload["requires_follow_up"])
        elif "follow_up_required" in payload:
            requires_follow_up = bool(payload["follow_up_required"])

        data = {
            "observation_id": obs_id,
            "event_id": event_id,
            "event_type": event_type,
            "source": normalized.get("source", "unknown"),
            "timestamp": normalized["timestamp"],
            "status": "recorded",
            "duplicate": False,
            "requires_follow_up": requires_follow_up,
            "follow_up_required": requires_follow_up,
            "follow_up_capability": None,  # Strictly NO autonomous planning trigger
        }

        return EngineResult(
            data=data,
            proposed_destination=None,
            proposed_capability=None,
            is_terminal=True,
        )

    async def list_observations(
        self,
        context: BrainContext,
        cursor: Optional[str] = None,
        limit: int = 50,
        filters: Optional[dict[str, Any]] = None,
    ) -> ObservationFeedResult:
        """Query observations using HMAC-signed keyset pagination."""
        if not context or not context.organization_id:
            raise ValueError("Valid BrainContext with organization_id required")

        filter_dict = filters or {}
        cursor_data = None
        if cursor:
            # Validates HMAC signature, org_id, case_id, and filter_hash integrity
            cursor_data = decode_and_verify_cursor(
                cursor=cursor,
                expected_org_id=context.organization_id,
                expected_case_id=context.case_id,
                expected_filter_dict=filter_dict,
                expected_sort="desc",
            )

        items: list[dict[str, Any]] = []
        has_more = False
        next_cursor = None

        if self._db_session_factory:
            session: Session = self._db_session_factory()
            try:
                query = session.query(Observation).filter(
                    Observation.organization_id == context.organization_id
                )
                if context.case_id:
                    query = query.filter(Observation.case_id == context.case_id)

                if "event_type" in filter_dict:
                    query = query.filter(Observation.event_type == filter_dict["event_type"])
                if "source" in filter_dict:
                    query = query.filter(Observation.source == filter_dict["source"])

                # Keyset condition if cursor provided: (created_at, id) < (cursor_created_at, cursor_id)
                if cursor_data:
                    query = query.filter(
                        or_(
                            Observation.created_at < cursor_data.created_at,
                            and_(
                                Observation.created_at == cursor_data.created_at,
                                Observation.id < cursor_data.id,
                            ),
                        )
                    )

                query = query.order_by(Observation.created_at.desc(), Observation.id.desc())
                records = query.limit(limit + 1).all()

                if len(records) > limit:
                    has_more = True
                    records = records[:limit]

                for r in records:
                    items.append({
                        "id": str(r.id),
                        "event_id": r.event_id,
                        "event_type": r.event_type,
                        "source": r.source,
                        "case_id": r.case_id,
                        "organization_id": r.organization_id,
                        "payload": r.payload,
                        "metadata": r.metadata_,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    })

                if has_more and records:
                    last = records[-1]
                    next_cursor = encode_cursor(
                        org_id=context.organization_id,
                        case_id=context.case_id,
                        filter_dict=filter_dict,
                        sort="desc",
                        created_at=last.created_at,
                        id=last.id,
                    )
            finally:
                session.close()
        else:
            # In-memory feed
            filtered = [
                obs for obs in self._in_memory_observations
                if obs.get("organization_id") == context.organization_id
                and (not context.case_id or obs.get("case_id") == context.case_id)
            ]
            if "event_type" in filter_dict:
                filtered = [obs for obs in filtered if obs.get("event_type") == filter_dict["event_type"]]
            if "source" in filter_dict:
                filtered = [obs for obs in filtered if obs.get("source") == filter_dict["source"]]

            # Sort descending by timestamp
            filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            start_idx = 0
            if cursor_data:
                # Find index of cursor
                for i, obs in enumerate(filtered):
                    if obs.get("observation_id") == str(cursor_data.id):
                        start_idx = i + 1
                        break

            sliced = filtered[start_idx : start_idx + limit + 1]
            if len(sliced) > limit:
                has_more = True
                sliced = sliced[:limit]

            for s in sliced:
                items.append({
                    "id": s.get("observation_id"),
                    "event_id": s.get("event_id"),
                    "event_type": s.get("event_type"),
                    "source": s.get("source"),
                    "case_id": s.get("case_id"),
                    "organization_id": s.get("organization_id"),
                    "payload": s.get("payload"),
                    "metadata": s.get("metadata"),
                    "created_at": s.get("timestamp"),
                })

            if has_more and sliced:
                last_s = sliced[-1]
                t_str = last_s.get("timestamp")
                dt = datetime.fromisoformat(t_str) if t_str else datetime.now(timezone.utc)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                uid_val = uuid.UUID(last_s["observation_id"]) if "observation_id" in last_s else uuid.uuid4()
                next_cursor = encode_cursor(
                    org_id=context.organization_id,
                    case_id=context.case_id,
                    filter_dict=filter_dict,
                    sort="desc",
                    created_at=dt,
                    id=uid_val,
                )

        return ObservationFeedResult(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
            total_count=len(items),
        )

    # -----------------------------------------------------------------
    # Capability handler (Mesh Adapter for Backward Compatibility)
    # -----------------------------------------------------------------

    async def handle_record_event(self, request: MeshRequest) -> MeshResponse:
        """Record an event as a normalized observation via mesh adapter.
        
        Strictly observes and records. Does NOT autonomously start PlanningEngine.
        """
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

        # Normalize
        normalized = self._normalize_event(payload, event_id)

        # Duplicate check
        idempotency_key = payload.get("idempotency_key") or event_id
        duplicate = await self._check_duplicate(idempotency_key, request)
        if duplicate is not None:
            return duplicate

        # Persist
        observation_id = await self._persist_observation(
            normalized, request, idempotency_key
        )

        # Determine follow-up
        if "requires_follow_up" in payload:
            requires_follow_up = bool(payload["requires_follow_up"])
        elif "follow_up_required" in payload:
            requires_follow_up = bool(payload["follow_up_required"])
        else:
            requires_follow_up = self._should_follow_up(event_type)

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
                delegated_result = {
                    "capability": target_cap,
                    "status": "error",
                    "error": str(exc),
                }

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
            "follow_up_capability": "planning.create_plan" if requires_follow_up else None,
        }
        if delegated_result is not None:
            result_payload["delegated_result"] = delegated_result

        return self._success(request, result_payload)

    # -----------------------------------------------------------------
    # Deterministic core & Helpers
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

    async def _check_duplicate_id(self, idempotency_key: str) -> Optional[str]:
        """Check duplicate by idempotency key returning existing observation ID if found."""
        if self._db_session_factory:
            session: Session = self._db_session_factory()
            try:
                existing = (
                    session.query(Observation)
                    .filter(Observation.idempotency_key == idempotency_key)
                    .first()
                )
                if existing:
                    return str(existing.id)
            finally:
                session.close()
        else:
            for obs in self._in_memory_observations:
                if obs.get("idempotency_key") == idempotency_key:
                    return obs.get("observation_id", "")
        return None

    async def _check_duplicate(
        self,
        idempotency_key: str,
        request: MeshRequest,
    ) -> Optional[MeshResponse]:
        """Check for duplicate observations using the idempotency key for mesh requests."""
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

    async def _persist_observation_data(
        self,
        normalized: dict[str, Any],
        context: BrainContext,
        idempotency_key: str,
        trace_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """Persist observation with verified BrainContext."""
        observation_id = str(uuid.uuid4())
        if self._db_session_factory:
            session: Session = self._db_session_factory()
            try:
                obs = Observation(
                    event_id=normalized["event_id"],
                    event_type=normalized["event_type"],
                    source=normalized["source"],
                    actor_ref=normalized.get("actor_ref") or context.user_id,
                    case_id=context.case_id,
                    organization_id=context.organization_id,
                    payload=normalized.get("payload"),
                    metadata_=normalized.get("metadata"),
                    trace_id=trace_id,
                    task_id=task_id,
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
                "case_id": context.case_id,
                "organization_id": context.organization_id,
                **normalized,
            })
        return observation_id

    async def _persist_observation(
        self,
        normalized: dict[str, Any],
        request: MeshRequest,
        idempotency_key: str,
    ) -> str:
        """Persist the observation for mesh requests."""
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
                "case_id": case_id,
                "organization_id": organization_id,
                **normalized,
            })

        return observation_id

    @staticmethod
    def _should_follow_up(event_type: str) -> bool:
        """Determine whether an event requires follow-up work."""
        if event_type in _RECORD_ONLY_EVENT_TYPES:
            return False
        if event_type in _FOLLOW_UP_EVENT_TYPES:
            return True
        return False
