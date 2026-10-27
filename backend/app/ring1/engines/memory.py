"""Basic Memory Engine — stores and retrieves Ring 1 memory records.

Deterministic Core:
- Enforce contextual boundaries on all writes and reads (case_id isolation)
- Store memory records with context_ref, trace_id, task_id, and payload
- Deduplicate via idempotency_key
- Retrieve records by ID with context validation
- In-memory fallback when database session is not configured

Intelligence Layer:
- Tag or categorize memory records when record_type is unspecified

Must not: cross context boundaries, leak records between cases,
allow unauthorized writes, fabricate record IDs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ring1.contracts.capabilities import (
    MEMORY_GET_RECORD,
    MEMORY_STORE_RECORD,
    CapabilityRegistry,
)
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.base import BaseEngine
from app.ring1.models.observation import MemoryRecord


class BasicMemoryEngine(BaseEngine):
    """Ring 1 Basic Memory Engine [GB].

    Provides context-isolated persistence and retrieval for Ring 1 records.
    Every stored and retrieved record is strictly scoped by context_ref and case_id.
    """

    def __init__(self, db_session_factory=None, **kwargs):
        super().__init__(**kwargs)
        self._db_session_factory = db_session_factory
        self._in_memory_records: dict[str, dict[str, Any]] = {}

    @property
    def engine_name(self) -> str:
        return "memory"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        registry.register(
            MEMORY_STORE_RECORD,
            self.engine_name,
            self.handle_store_record,
            description="Store a context-scoped memory record with idempotency support.",
        )
        registry.register(
            MEMORY_GET_RECORD,
            self.engine_name,
            self.handle_get_record,
            description="Retrieve a memory record by ID with context boundary enforcement.",
        )

    # -----------------------------------------------------------------
    # Capability: memory.store_record
    # -----------------------------------------------------------------

    async def handle_store_record(self, request: MeshRequest) -> MeshResponse:
        """Store a new memory record, enforcing context isolation and idempotency.

        Payload expected:
        - record_type: str (required, e.g. "observation", "task_result", "fact")
        - payload: dict (the data to store)
        - metadata: dict (optional)
        - idempotency_key: str (optional)
        - source_observation_id: str/uuid (optional)
        - case_id: str (optional, defaults to request.context_ref.case_id)
        """
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        # Enforce context boundary
        context_err = self.require_context_ref(request)
        if context_err:
            return context_err

        context_ref = request.context_ref
        case_id = request.payload.get("case_id") or (
            context_ref.case_id if context_ref else None
        )
        org_id = context_ref.organization_id if context_ref else None

        record_type = request.payload.get("record_type")
        payload = request.payload.get("payload")
        if payload is None:
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.INVALID_PAYLOAD,
                "Missing required 'payload' in memory store request.",
            )

        # Intelligence Layer fallback for missing record_type
        if not record_type:
            record_type = await self._infer_record_type(payload)

        idempotency_key = request.payload.get("idempotency_key")
        metadata = request.payload.get("metadata") or {}
        source_obs_id = request.payload.get("source_observation_id")

        if self._db_session_factory is not None:
            return await self._store_in_db(
                request=request,
                record_type=record_type,
                payload=payload,
                metadata=metadata,
                context_ref_str=context_ref.ref if context_ref else None,
                case_id=case_id,
                organization_id=org_id,
                idempotency_key=idempotency_key,
                source_obs_id=source_obs_id,
            )
        else:
            return self._store_in_memory(
                request=request,
                record_type=record_type,
                payload=payload,
                metadata=metadata,
                context_ref_str=context_ref.ref if context_ref else None,
                case_id=case_id,
                organization_id=org_id,
                idempotency_key=idempotency_key,
                source_obs_id=source_obs_id,
            )

    # -----------------------------------------------------------------
    # Capability: memory.get_record
    # -----------------------------------------------------------------

    async def handle_get_record(self, request: MeshRequest) -> MeshResponse:
        """Retrieve a memory record by record_id, enforcing context isolation.

        Payload expected:
        - record_id: str / uuid
        - case_id: str (optional, enforced against record's case_id if present)
        """
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        record_id = request.payload.get("record_id")
        if not record_id:
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.INVALID_PAYLOAD,
                "Missing required 'record_id' in memory get request.",
            )

        expected_case_id = request.payload.get("case_id") or (
            request.context_ref.case_id if request.context_ref else None
        )

        if self._db_session_factory is not None:
            return await self._get_from_db(
                request=request,
                record_id=record_id,
                expected_case_id=expected_case_id,
            )
        else:
            return self._get_from_memory(
                request=request,
                record_id=record_id,
                expected_case_id=expected_case_id,
            )

    # -----------------------------------------------------------------
    # Database persistence
    # -----------------------------------------------------------------

    async def _store_in_db(
        self,
        request: MeshRequest,
        record_type: str,
        payload: dict[str, Any],
        metadata: dict[str, Any],
        context_ref_str: Optional[str],
        case_id: Optional[str],
        organization_id: Optional[str],
        idempotency_key: Optional[str],
        source_obs_id: Optional[str],
    ) -> MeshResponse:
        session: Session = self._db_session_factory()
        try:
            # Check idempotency
            if idempotency_key:
                stmt = select(MemoryRecord).where(
                    MemoryRecord.idempotency_key == idempotency_key
                )
                existing = session.execute(stmt).scalar_one_or_none()
                if existing:
                    return self._success(
                        request,
                        {
                            "record_id": str(existing.id),
                            "record_type": existing.record_type,
                            "status": existing.status,
                            "duplicate": True,
                            "context_ref": existing.context_ref,
                            "case_id": existing.case_id,
                        },
                        context_ref=existing.context_ref,
                    )

            parsed_obs_id = None
            if source_obs_id:
                try:
                    parsed_obs_id = uuid.UUID(str(source_obs_id))
                except (ValueError, TypeError):
                    parsed_obs_id = None

            record = MemoryRecord(
                record_type=record_type,
                context_ref=context_ref_str,
                case_id=case_id,
                organization_id=organization_id,
                payload=payload,
                metadata_=metadata,
                trace_id=request.trace_id,
                task_id=request.task_id,
                source_observation_id=parsed_obs_id,
                idempotency_key=idempotency_key,
                status="active",
            )
            session.add(record)
            session.commit()
            session.refresh(record)

            return self._success(
                request,
                {
                    "record_id": str(record.id),
                    "record_type": record.record_type,
                    "status": record.status,
                    "duplicate": False,
                    "context_ref": record.context_ref,
                    "case_id": record.case_id,
                    "created_at": record.created_at.isoformat(),
                },
                context_ref=record.context_ref,
            )
        except Exception as exc:
            session.rollback()
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.INTERNAL_EXECUTION_ERROR,
                f"Failed to persist memory record: {str(exc)}",
            )
        finally:
            session.close()

    async def _get_from_db(
        self,
        request: MeshRequest,
        record_id: str,
        expected_case_id: Optional[str],
    ) -> MeshResponse:
        session: Session = self._db_session_factory()
        try:
            try:
                parsed_id = uuid.UUID(str(record_id))
            except (ValueError, TypeError):
                return self._error(
                    request,
                    ResultStatus.INVALID_REQUEST,
                    EngineErrorCode.INVALID_PAYLOAD,
                    f"Invalid record_id UUID: '{record_id}'",
                )

            stmt = select(MemoryRecord).where(MemoryRecord.id == parsed_id)
            record = session.execute(stmt).scalar_one_or_none()
            if not record:
                return self._error(
                    request,
                    ResultStatus.FAILED,
                    EngineErrorCode.DATA_NOT_FOUND,
                    f"Memory record '{record_id}' not found.",
                )

            # Enforce case isolation: prevent cross-context access
            if expected_case_id and record.case_id and record.case_id != expected_case_id:
                return self._error(
                    request,
                    ResultStatus.FAILED,
                    EngineErrorCode.AUTHORIZATION_DENIED,
                    f"Access denied: record belongs to case '{record.case_id}', not '{expected_case_id}'.",
                )

            return self._success(
                request,
                {
                    "record_id": str(record.id),
                    "record_type": record.record_type,
                    "context_ref": record.context_ref,
                    "case_id": record.case_id,
                    "organization_id": record.organization_id,
                    "payload": record.payload,
                    "metadata": record.metadata_,
                    "trace_id": record.trace_id,
                    "task_id": record.task_id,
                    "status": record.status,
                    "created_at": record.created_at.isoformat(),
                },
                context_ref=record.context_ref,
            )
        finally:
            session.close()

    # -----------------------------------------------------------------
    # In-memory persistence
    # -----------------------------------------------------------------

    def _store_in_memory(
        self,
        request: MeshRequest,
        record_type: str,
        payload: dict[str, Any],
        metadata: dict[str, Any],
        context_ref_str: Optional[str],
        case_id: Optional[str],
        organization_id: Optional[str],
        idempotency_key: Optional[str],
        source_obs_id: Optional[str],
    ) -> MeshResponse:
        # Check idempotency
        if idempotency_key:
            for rec in self._in_memory_records.values():
                if rec.get("idempotency_key") == idempotency_key:
                    return self._success(
                        request,
                        {
                            "record_id": rec["record_id"],
                            "record_type": rec["record_type"],
                            "status": rec["status"],
                            "duplicate": True,
                            "context_ref": rec["context_ref"],
                            "case_id": rec["case_id"],
                        },
                        context_ref=rec["context_ref"],
                    )

        rec_id = str(uuid.uuid4())
        record = {
            "record_id": rec_id,
            "record_type": record_type,
            "context_ref": context_ref_str,
            "case_id": case_id,
            "organization_id": organization_id,
            "payload": payload,
            "metadata": metadata,
            "trace_id": request.trace_id,
            "task_id": request.task_id,
            "source_observation_id": source_obs_id,
            "idempotency_key": idempotency_key,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._in_memory_records[rec_id] = record

        return self._success(
            request,
            {
                "record_id": rec_id,
                "record_type": record_type,
                "status": "active",
                "duplicate": False,
                "context_ref": context_ref_str,
                "case_id": case_id,
                "created_at": record["created_at"],
            },
            context_ref=context_ref_str,
        )

    def _get_from_memory(
        self,
        request: MeshRequest,
        record_id: str,
        expected_case_id: Optional[str],
    ) -> MeshResponse:
        rec = self._in_memory_records.get(record_id)
        if not rec:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.DATA_NOT_FOUND,
                f"Memory record '{record_id}' not found.",
            )

        if expected_case_id and rec.get("case_id") and rec["case_id"] != expected_case_id:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                f"Access denied: record belongs to case '{rec['case_id']}', not '{expected_case_id}'.",
            )

        return self._success(
            request,
            {
                "record_id": rec["record_id"],
                "record_type": rec["record_type"],
                "context_ref": rec["context_ref"],
                "case_id": rec["case_id"],
                "organization_id": rec["organization_id"],
                "payload": rec["payload"],
                "metadata": rec["metadata"],
                "trace_id": rec["trace_id"],
                "task_id": rec["task_id"],
                "status": rec["status"],
                "created_at": rec["created_at"],
            },
            context_ref=rec["context_ref"],
        )

    # -----------------------------------------------------------------
    # Intelligence layer
    # -----------------------------------------------------------------

    async def _infer_record_type(self, payload: dict[str, Any]) -> str:
        """Deterministically guess record type or use LLM if needed."""
        if "event_type" in payload:
            return "observation"
        if "plan_id" in payload:
            return "plan"
        if "query" in payload:
            return "search_query"
        return "general_fact"
