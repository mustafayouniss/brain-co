"""Mesh Event Service for Canonical Lifecycle Telemetry & Dual Delivery.

Guarantees:
1. Canonical lifecycle event types stamped with sequence, duration, plan version,
   organization_id, and case_id.
2. Dual delivery: returns event dictionary for synchronous execution (SSE)
   AND broadcasts to real-time WebSocket subscribers via ws_manager.
3. Durable persistence to PostgreSQL mesh_events table when available.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Optional
import uuid
from uuid import UUID

from sqlalchemy.exc import ProgrammingError, OperationalError
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.ws_manager import ws_manager
from app.models.mesh_event import MeshEventRecord

logger = logging.getLogger("app.services.mesh_event_service")


class MeshLifecycleEventType:
    """Canonical Ring 1 / General Brain lifecycle event types."""
    TASK_CREATED = "task_created"
    TASK_DISPATCHED = "task_dispatched"
    TASK_RECEIVED = "task_received"
    CONTEXT_RETRIEVED = "context_retrieved"
    TOOL_INVOKED = "tool_invoked"
    TOOL_COMPLETED = "tool_completed"
    HANDOFF_EVALUATED = "handoff_evaluated"
    OBSERVATION_PERSISTED = "observation_persisted"
    MEMORY_PERSISTED = "memory_persisted"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRY = "task_retry"


class MeshEventService:
    """Service managing mesh lifecycle events, dual delivery, and persistence."""

    @staticmethod
    async def record_and_broadcast(
        session: Optional[Session],
        run_id: str | UUID,
        sequence_number: int,
        organization_id: str,
        event_type: str,
        status: str,
        source_engine: str,
        destination_engine: Optional[str] = None,
        capability: Optional[str] = None,
        case_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
        plan_version: Optional[int] = None,
        payload: Optional[dict[str, Any]] = None,
        error_details: Optional[str] = None,
        broadcast: bool = True,
    ) -> dict[str, Any]:
        """Record lifecycle event, persist to database if available, and broadcast."""
        run_uuid = run_id if isinstance(run_id, UUID) else None
        if not run_uuid:
            try:
                # Handle run-xxxx strings by hashing or creating UUID
                clean_str = str(run_id).replace("run-", "").replace("pdf-run-", "")
                if len(clean_str) < 32:
                    clean_str = clean_str.ljust(32, "0")
                run_uuid = UUID(clean_str[:32])
            except Exception:
                run_uuid = uuid.uuid4()

        clean_case_id = case_id.strip() if case_id and case_id.strip() else None
        iso_now = datetime.now(timezone.utc).isoformat()

        event_dict: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "run_id": str(run_id),
            "sequence_number": sequence_number,
            "organization_id": organization_id,
            "case_id": clean_case_id,
            "source_engine": source_engine,
            "destination_engine": destination_engine,
            "capability": capability,
            "event_type": event_type,
            "status": status,
            "duration_ms": duration_ms,
            "plan_version": plan_version,
            "payload": payload or {},
            "error_details": error_details,
            "timestamp": iso_now,
            "is_persisted": False,
        }

        # 1. Durable persistence if database session provided
        if session:
            try:
                record = MeshEventRecord(
                    id=UUID(event_dict["id"]),
                    run_id=run_uuid,
                    sequence_number=sequence_number,
                    organization_id=organization_id,
                    case_id=clean_case_id,
                    source_engine=source_engine,
                    destination_engine=destination_engine,
                    capability=capability,
                    event_type=event_type,
                    status=status,
                    duration_ms=duration_ms,
                    plan_version=plan_version,
                    payload=payload,
                    error_details=error_details,
                )
                session.add(record)
                session.flush()
                event_dict["is_persisted"] = True
            except (ProgrammingError, OperationalError) as exc:
                # Safe fallback if mesh_events table not yet migrated on active connection
                session.rollback()
                logger.debug("MeshEvent persistence skipped (table not ready): %s", exc)
            except Exception as exc:
                session.rollback()
                logger.warning("Failed to persist MeshEventRecord: %s", exc)

        # 2. Dual Delivery: Real-Time WebSocket broadcast
        if broadcast:
            try:
                await ws_manager.broadcast_event(
                    organization_id=organization_id,
                    event_payload=event_dict,
                    case_id=clean_case_id,
                )
            except Exception as exc:
                logger.warning("Failed to broadcast mesh event via ws_manager: %s", exc)

        return event_dict

    @staticmethod
    def get_events(
        session: Session,
        organization_id: str,
        case_id: Optional[str] = None,
        run_id: Optional[UUID | str] = None,
        since_sequence: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve historical lifecycle events with monotonic ordering and scoping.
        
        Guarantees strict tenant boundary (organization_id) and optional case/run filters.
        Supports cursor-based incremental replay for reconnecting WebSocket/SSE clients.
        """
        try:
            stmt = sa.select(MeshEventRecord).where(
                MeshEventRecord.organization_id == organization_id.strip()
            )
            if case_id and case_id.strip():
                stmt = stmt.where(MeshEventRecord.case_id == case_id.strip())

            if run_id:
                try:
                    run_uuid = run_id if isinstance(run_id, UUID) else None
                    if not run_uuid:
                        clean_str = str(run_id).replace("run-", "").replace("pdf-run-", "").ljust(32, "0")[:32]
                        run_uuid = UUID(clean_str)
                    stmt = stmt.where(MeshEventRecord.run_id == run_uuid)
                except Exception:
                    pass

            if since_sequence is not None:
                stmt = stmt.where(MeshEventRecord.sequence_number > since_sequence)

            stmt = stmt.order_by(MeshEventRecord.sequence_number.asc()).limit(min(limit, 500))
            records = session.scalars(stmt).all()
            return [
                {
                    "id": str(r.id),
                    "run_id": str(r.run_id),
                    "sequence_number": r.sequence_number,
                    "organization_id": r.organization_id,
                    "case_id": r.case_id,
                    "source_engine": r.source_engine,
                    "destination_engine": r.destination_engine,
                    "capability": r.capability,
                    "event_type": r.event_type,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "plan_version": r.plan_version,
                    "payload": r.payload or {},
                    "error_details": r.error_details,
                    "timestamp": r.created_at.isoformat() if r.created_at else None,
                    "is_persisted": True,
                }
                for r in records
            ]
        except (ProgrammingError, OperationalError):
            session.rollback()
            return []
