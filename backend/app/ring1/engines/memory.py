"""Basic Memory Engine — stores and retrieves Ring 1 memory records.

Deterministic Core:
- Enforce contextual boundaries on all writes and reads (case_id isolation)
- Store memory records with context_ref, trace_id, task_id, and payload
- Manage knowledge candidate lifecycle: CANDIDATE -> VALIDATED / REJECTED
- Enforce human validation authority over candidate promotion
- Reject automatic self-promotion of candidates into validated knowledge
- Deduplicate via idempotency_key
- Retrieve records by ID with context validation
- In-memory fallback when database session is not configured

Intelligence Layer:
- Tag or categorize memory records when record_type is unspecified

Must not: cross context boundaries, leak records between cases,
allow unauthorized writes, permit self-validation of candidates.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import BrainContext
from app.ring1.contracts.capabilities import (
    MEMORY_GET_RECORD,
    MEMORY_STORE_RECORD,
    CapabilityRegistry,
)
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.protocols import EngineResult, IMemoryEngine
from app.ring1.engines.base import BaseEngine
from app.ring1.models.observation import MemoryRecord


class BasicMemoryEngine(BaseEngine, IMemoryEngine):
    """Ring 1 Basic Memory Engine [GB].

    Provides context-isolated persistence and candidate lifecycle management.
    Preserves human validation authority over knowledge candidates.
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
    # Pure Engine Protocol implementation (Decoupled from Transport)
    # -----------------------------------------------------------------

    async def store_candidate(
        self,
        fact_data: dict[str, Any],
        context: BrainContext,
    ) -> EngineResult:
        """Store a new knowledge candidate in the CANDIDATE lifecycle state.
        
        Candidates are never automatically promoted to validated knowledge.
        """
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )
        if not context.case_id or not str(context.case_id).strip():
            return EngineResult(
                error={"code": "CONTEXT_MISSING", "message": "Non-empty case_id required for memory candidates"}
            )

        payload = fact_data.get("payload", fact_data)
        record_type = fact_data.get("record_type", "fact_candidate")
        idempotency_key = fact_data.get("idempotency_key")
        metadata = dict(fact_data.get("metadata", {}))
        metadata["lifecycle_state"] = "candidate"
        source_obs_id = fact_data.get("source_observation_id")

        if self._db_session_factory is not None:
            session: Session = self._db_session_factory()
            try:
                if idempotency_key:
                    stmt = select(MemoryRecord).where(MemoryRecord.idempotency_key == idempotency_key)
                    existing = session.execute(stmt).scalar_one_or_none()
                    if existing:
                        return EngineResult(
                            data={
                                "record_id": str(existing.id),
                                "record_type": existing.record_type,
                                "status": existing.status,
                                "duplicate": True,
                                "case_id": existing.case_id,
                            }
                        )

                parsed_obs_id = None
                if source_obs_id:
                    try:
                        parsed_obs_id = UUID(str(source_obs_id))
                    except (ValueError, TypeError):
                        parsed_obs_id = None

                record = MemoryRecord(
                    record_type=record_type,
                    context_ref=f"ctx-{context.case_id}",
                    case_id=context.case_id,
                    organization_id=context.organization_id,
                    payload=payload,
                    metadata_=metadata,
                    trace_id=fact_data.get("trace_id"),
                    task_id=fact_data.get("task_id"),
                    source_observation_id=parsed_obs_id,
                    idempotency_key=idempotency_key,
                    status="candidate",
                )
                session.add(record)
                session.commit()
                session.refresh(record)

                return EngineResult(
                    data={
                        "record_id": str(record.id),
                        "record_type": record.record_type,
                        "status": "candidate",
                        "case_id": record.case_id,
                        "organization_id": record.organization_id,
                        "created_at": record.created_at.isoformat(),
                    },
                    is_terminal=True,
                )
            except Exception as exc:
                session.rollback()
                return EngineResult(error={"code": "PERSISTENCE_ERROR", "message": str(exc)})
            finally:
                session.close()
        else:
            rec_id = str(uuid.uuid4())
            record = {
                "record_id": rec_id,
                "record_type": record_type,
                "case_id": context.case_id,
                "organization_id": context.organization_id,
                "payload": payload,
                "metadata": metadata,
                "status": "candidate",
                "idempotency_key": idempotency_key,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._in_memory_records[rec_id] = record
            return EngineResult(data=record, is_terminal=True)

    async def get_record(
        self,
        record_id: UUID,
        context: BrainContext,
    ) -> EngineResult:
        """Retrieve a memory record enforcing strict case and org isolation."""
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )
        if not context.case_id or not str(context.case_id).strip():
            return EngineResult(
                error={"code": "CONTEXT_MISSING", "message": "Non-empty case_id required for memory reads"}
            )

        rec_id_str = str(record_id)
        if self._db_session_factory is not None:
            session: Session = self._db_session_factory()
            try:
                stmt = select(MemoryRecord).where(MemoryRecord.id == record_id)
                record = session.execute(stmt).scalar_one_or_none()
                if (
                    not record
                    or (record.case_id and record.case_id != context.case_id)
                    or (record.organization_id and record.organization_id != context.organization_id)
                ):
                    return EngineResult(
                        error={
                            "code": "PERMISSION_DENIED",
                            "message": "Access denied: unauthorized context or record does not exist",
                        }
                    )

                return EngineResult(
                    data={
                        "record_id": str(record.id),
                        "record_type": record.record_type,
                        "case_id": record.case_id,
                        "organization_id": record.organization_id,
                        "payload": record.payload,
                        "metadata": record.metadata_,
                        "status": record.status,
                        "created_at": record.created_at.isoformat() if record.created_at else None,
                    }
                )
            finally:
                session.close()
        else:
            rec = self._in_memory_records.get(rec_id_str)
            if (
                not rec
                or (rec.get("case_id") and rec["case_id"] != context.case_id)
                or (rec.get("organization_id") and rec["organization_id"] != context.organization_id)
            ):
                return EngineResult(
                    error={
                        "code": "PERMISSION_DENIED",
                        "message": "Access denied: unauthorized context or record does not exist",
                    }
                )
            return EngineResult(data=rec)

    async def validate_candidate(
        self,
        record_id: UUID,
        action: str,  # "VALIDATE" or "REJECT"
        context: BrainContext,
    ) -> EngineResult:
        """Validate or reject a knowledge candidate.
        
        Requires explicit human validation authority (context.validation_authority == True).
        Self-promotion is strictly rejected.
        """
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )

        # Enforce human validation authority
        if not context.validation_authority:
            return EngineResult(
                error={
                    "code": "VALIDATION_AUTHORITY_REQUIRED",
                    "message": "Human validation authority required to promote or reject candidates. Automatic self-validation is strictly forbidden.",
                }
            )

        act = action.strip().upper()
        if act not in ("VALIDATE", "REJECT"):
            return EngineResult(
                error={"code": "INVALID_ACTION", "message": f"Action must be 'VALIDATE' or 'REJECT', got '{action}'"}
            )

        new_status = "validated" if act == "VALIDATE" else "rejected"

        if self._db_session_factory is not None:
            session: Session = self._db_session_factory()
            try:
                stmt = select(MemoryRecord).where(MemoryRecord.id == record_id)
                record = session.execute(stmt).scalar_one_or_none()
                if (
                    not record
                    or (record.case_id and context.case_id and record.case_id != context.case_id)
                    or (record.organization_id and record.organization_id != context.organization_id)
                ):
                    return EngineResult(
                        error={"code": "PERMISSION_DENIED", "message": "Record not found or access denied"}
                    )

                record.status = new_status
                if record.metadata_ is None:
                    record.metadata_ = {}
                meta = dict(record.metadata_)
                meta["validated_by"] = context.user_id or "human_validator"
                meta["validated_at"] = datetime.now(timezone.utc).isoformat()
                record.metadata_ = meta

                session.commit()
                return EngineResult(
                    data={
                        "record_id": str(record.id),
                        "status": new_status,
                        "action": act,
                        "metadata": meta,
                    }
                )
            except Exception as e:
                session.rollback()
                return EngineResult(error={"code": "UPDATE_ERROR", "message": str(e)})
            finally:
                session.close()
        else:
            rec_id_str = str(record_id)
            rec = self._in_memory_records.get(rec_id_str)
            if not rec or (rec.get("organization_id") and rec["organization_id"] != context.organization_id):
                return EngineResult(error={"code": "PERMISSION_DENIED", "message": "Record not found or access denied"})
            rec["status"] = new_status
            rec["validated_by"] = context.user_id or "human_validator"
            return EngineResult(
                data={
                    "record_id": rec_id_str,
                    "status": new_status,
                    "action": act,
                    "metadata": {"validated_by": rec["validated_by"]},
                }
            )

    # -----------------------------------------------------------------
    # Capability: memory.store_record (Mesh Adapter for Backward Compatibility)
    # -----------------------------------------------------------------

    async def handle_store_record(self, request: MeshRequest) -> MeshResponse:
        """Store a new memory record, enforcing context isolation and idempotency."""
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        context_err = self.require_context_ref(request)
        if context_err:
            return context_err

        context_ref = request.context_ref
        if not context_ref or not (context_ref.case_id or "").strip():
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A valid context_ref with non-empty case_id is required for memory writes.",
            )

        if not (context_ref.organization_id or "").strip():
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A valid context_ref with non-empty organization_id is required for memory writes.",
            )

        authorized_case_id = context_ref.case_id.strip()
        authorized_org_id = context_ref.organization_id.strip()

        payload_case_id = request.payload.get("case_id")
        if payload_case_id and str(payload_case_id).strip() != authorized_case_id:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                "Access denied: payload case_id does not match authorized context.",
            )

        payload_org_id = request.payload.get("organization_id")
        if payload_org_id and str(payload_org_id).strip() != authorized_org_id:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                "Access denied: payload organization_id does not match authorized context.",
            )

        record_type = request.payload.get("record_type")
        payload = request.payload.get("payload")
        if payload is None:
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.INVALID_PAYLOAD,
                "Missing required 'payload' in memory store request.",
            )

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
                case_id=authorized_case_id,
                organization_id=authorized_org_id,
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
                case_id=authorized_case_id,
                organization_id=authorized_org_id,
                idempotency_key=idempotency_key,
                source_obs_id=source_obs_id,
            )

    # -----------------------------------------------------------------
    # Capability: memory.get_record (Mesh Adapter for Backward Compatibility)
    # -----------------------------------------------------------------

    async def handle_get_record(self, request: MeshRequest) -> MeshResponse:
        """Retrieve a memory record by record_id, enforcing context isolation."""
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        context_err = self.require_context_ref(request)
        if context_err:
            return context_err

        context_ref = request.context_ref
        if not context_ref or not (context_ref.case_id or "").strip():
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A valid context_ref with non-empty case_id is required for memory reads.",
            )

        if not (context_ref.organization_id or "").strip():
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A valid context_ref with non-empty organization_id is required for memory reads.",
            )

        record_id = request.payload.get("record_id")
        if not record_id or not str(record_id).strip():
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.INVALID_PAYLOAD,
                "Missing required 'record_id' in memory get request.",
            )

        authorized_case_id = context_ref.case_id.strip()
        authorized_org_id = context_ref.organization_id.strip()

        payload_case_id = request.payload.get("case_id")
        if payload_case_id and str(payload_case_id).strip() != authorized_case_id:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                "Access denied: payload case_id does not match authorized context.",
            )

        payload_org_id = request.payload.get("organization_id")
        if payload_org_id and str(payload_org_id).strip() != authorized_org_id:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                "Access denied: payload organization_id does not match authorized context.",
            )

        if self._db_session_factory is not None:
            return await self._get_from_db(
                request=request,
                record_id=str(record_id).strip(),
                authorized_case_id=authorized_case_id,
                authorized_org_id=authorized_org_id,
            )
        else:
            return self._get_from_memory(
                request=request,
                record_id=str(record_id).strip(),
                authorized_case_id=authorized_case_id,
                authorized_org_id=authorized_org_id,
            )

    # -----------------------------------------------------------------
    # Database persistence helpers
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
        authorized_case_id: str,
        authorized_org_id: str,
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
            if (
                not record
                or (record.case_id and record.case_id != authorized_case_id)
                or (record.organization_id and record.organization_id != authorized_org_id)
            ):
                return self._error(
                    request,
                    ResultStatus.FAILED,
                    EngineErrorCode.AUTHORIZATION_DENIED,
                    "Access denied: unauthorized context or record does not exist.",
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
        authorized_case_id: str,
        authorized_org_id: str,
    ) -> MeshResponse:
        rec = self._in_memory_records.get(record_id)
        if (
            not rec
            or (rec.get("case_id") and rec["case_id"] != authorized_case_id)
            or (rec.get("organization_id") and rec["organization_id"] != authorized_org_id)
        ):
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                "Access denied: unauthorized context or record does not exist.",
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
        if "event_type" in payload:
            return "observation"
        if "plan_id" in payload:
            return "plan"
        if "query" in payload:
            return "search_query"
        return "general_fact"
