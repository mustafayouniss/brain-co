"""Basic Memory Engine — stores and retrieves General Brain memory records.

Deterministic Core:
- Enforce contextual boundaries on all writes and reads (case_id / scope_id isolation)
- Store memory records with context_ref, trace_id, task_id, and payload via IMemoryStore
- Manage knowledge candidate lifecycle: CANDIDATE -> VALIDATED / REJECTED
- Enforce human validation authority over candidate promotion
- Reject automatic self-promotion of candidates into validated knowledge
- Deduplicate via idempotency_key
- Retrieve records by ID with scope validation

Intelligence Layer:
- Tag or categorize memory records when record_type is unspecified

Must not: cross context boundaries, leak records between cases,
allow unauthorized writes, permit self-validation of candidates,
or depend directly on database infrastructure.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from brain.general.contracts.capabilities import (
    MEMORY_GET_RECORD,
    MEMORY_STORE_RECORD,
    CapabilityRegistry,
)
from brain.general.contracts.context import BrainContext
from brain.general.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from brain.general.contracts.errors import EngineErrorCode, StorageConfigurationError
from brain.general.contracts.llm import ILLMClient
from brain.general.contracts.protocols import EngineResult, IMemoryEngine
from brain.general.contracts.storage import IMemoryStore
from brain.general.engines.base import BaseEngine
from brain.general.runtime.router import MeshRouter


class BasicMemoryEngine(BaseEngine, IMemoryEngine):
    """General Brain Basic Memory Engine [GB].

    Provides context-isolated persistence and candidate lifecycle management.
    Requires an explicit IMemoryStore implementation injected at initialization.
    Preserves human validation authority over knowledge candidates.
    """

    def __init__(
        self,
        store: Optional[IMemoryStore] = None,
        llm_client: Optional[ILLMClient] = None,
        mesh_router: Optional[MeshRouter] = None,
        llm_service: Optional[ILLMClient] = None,
        **kwargs: Any,
    ) -> None:
        if store is None:
            raise StorageConfigurationError(
                "BasicMemoryEngine requires an explicit IMemoryStore implementation. "
                "For test or CLI use, inject InMemoryMemoryStore(). "
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
    def store(self) -> IMemoryStore:
        return self._store

    @property
    def _in_memory_records(self) -> dict[str, dict[str, Any]]:
        if hasattr(self._store, "records"):
            return self._store.records
        return {}

    @property
    def engine_name(self) -> str:
        return "memory"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        registry.register(
            MEMORY_STORE_RECORD,
            self.engine_name,
            self.handle_store_record,
            description="Store a record with contextual boundary enforcement.",
        )
        registry.register(
            MEMORY_GET_RECORD,
            self.engine_name,
            self.handle_get_record,
            description="Retrieve a stored record by ID with context validation.",
        )

    # -----------------------------------------------------------------
    # Pure Engine Protocol implementation (Decoupled from Transport)
    # -----------------------------------------------------------------

    async def store_candidate(
        self,
        fact_data: dict[str, Any],
        context: BrainContext,
    ) -> EngineResult:
        """Store a candidate knowledge object within the authorized context scope."""
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )

        content = fact_data.get("content") or fact_data.get("fact") or fact_data.get("payload")
        if not content:
            return EngineResult(
                error={"code": EngineErrorCode.INVALID_PAYLOAD.value, "message": "Content is required for memory storage."}
            )

        record_id = fact_data.get("id") or str(uuid.uuid4())
        idempotency_key = fact_data.get("idempotency_key") or f"idemp-{record_id}"

        # 1. Duplicate check via store
        existing = await self._store.find_by_idempotency_key(idempotency_key)
        if existing:
            return EngineResult(
                data={
                    "record_id": str(existing.get("id") or existing.get("record_id")),
                    "record_type": existing.get("record_type"),
                    "status": existing.get("status"),
                    "duplicate": True,
                }
            )

        # 2. Tag / categorize if missing
        record_type = fact_data.get("record_type") or fact_data.get("type")
        if not record_type:
            record_type = await self._infer_record_type(str(content))

        # Enforce lifecycle invariant: New knowledge objects enter as 'candidate'
        initial_status = "candidate"
        # Only explicitly authorized validation authority in trusted backend context can store directly as validated
        if fact_data.get("status") == "validated" and context.validation_authority:
            initial_status = "validated"

        to_save = {
            "id": record_id,
            "record_id": record_id,
            "record_type": record_type,
            "content": content if isinstance(content, str) else str(content),
            "payload": content if isinstance(content, dict) else {"content": content},
            "status": initial_status,
            "confidence": float(fact_data.get("confidence", 0.9)),
            "source": fact_data.get("source", "perception"),
            "scope_level": fact_data.get("scope_level", "case" if context.effective_scope_id else "organization"),
            "organization_id": context.organization_id,
            "case_id": context.effective_scope_id,
            "scope_id": context.effective_scope_id,
            "task_id": context.task_id,
            "trace_id": context.correlation_id,
            "actor_ref": context.user_id,
            "idempotency_key": idempotency_key,
            "metadata": fact_data.get("metadata", {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        saved_id = await self._store.save_record(to_save)
        data = {
            "record_id": saved_id,
            "id": saved_id,
            "record_type": record_type,
            "status": initial_status,
            "scope_level": to_save["scope_level"],
            "case_id": context.effective_scope_id,
            "organization_id": context.organization_id,
            "confidence": to_save["confidence"],
            "duplicate": False,
        }
        return EngineResult(data=data)

    async def get_record(
        self,
        record_id: UUID | str,
        context: BrainContext,
    ) -> EngineResult:
        """Retrieve an authorized memory object by ID with strict scope boundaries."""
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )

        rec = await self._store.get_record(
            record_id=str(record_id),
            organization_id=context.organization_id,
            case_id=context.effective_scope_id,
        )

        if not rec:
            return EngineResult(
                error={"code": "PERMISSION_DENIED", "message": "Access denied: unauthorized context or record does not exist"}
            )

        return EngineResult(data=rec)

    async def validate_candidate(
        self,
        record_id: UUID | str,
        action: str,
        context: BrainContext,
    ) -> EngineResult:
        """Promote or reject a candidate knowledge object.
        
        Strictly enforces that the actor has validation authority (Ring 8 gate).
        Self-validation by engines or unauthorized actors is strictly rejected.
        """
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )

        if not context.validation_authority:
            return EngineResult(
                error={
                    "code": "VALIDATION_AUTHORITY_REQUIRED",
                    "message": "Human validation authority required to promote or reject candidates.",
                }
            )

        action_upper = action.strip().upper()
        if action_upper not in ("VALIDATE", "REJECT"):
            return EngineResult(
                error={"code": EngineErrorCode.INVALID_PAYLOAD.value, "message": "Action must be 'VALIDATE' or 'REJECT'."}
            )

        new_status = "validated" if action_upper == "VALIDATE" else "rejected"
        meta = {
            "validated_by": context.user_id,
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        success = await self._store.update_status(
            record_id=str(record_id),
            organization_id=context.organization_id,
            new_status=new_status,
            validation_authority=context.validation_authority,
            metadata=meta,
        )

        if not success:
            return EngineResult(
                error={"code": EngineErrorCode.RECORD_NOT_FOUND.value, "message": "Record not found or update denied."}
            )

        return EngineResult(
            data={
                "record_id": str(record_id),
                "status": new_status,
                "action": action_upper,
                "metadata": meta,
            }
        )

    # -----------------------------------------------------------------
    # Capability handlers (Mesh Adapter for Backward Compatibility)
    # -----------------------------------------------------------------

    async def handle_store_record(self, request: MeshRequest) -> MeshResponse:
        """Handle capability: memory.store_record, enforcing strict context boundaries."""
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        context_err = self.require_context_ref(request)
        if context_err:
            return context_err

        context_ref = request.context_ref
        if not context_ref or not (getattr(context_ref, "case_id", None) or "").strip():
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A valid context_ref with non-empty case_id is required for memory writes.",
            )

        if not (getattr(context_ref, "organization_id", None) or "").strip():
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

        if idempotency_key:
            existing = await self._store.find_by_idempotency_key(idempotency_key)
            if existing:
                return self._success(
                    request,
                    {
                        "record_id": existing.get("record_id") or existing.get("id"),
                        "record_type": existing.get("record_type"),
                        "status": existing.get("status", "active"),
                        "duplicate": True,
                        "context_ref": getattr(context_ref, "ref", str(context_ref)),
                        "case_id": existing.get("case_id", authorized_case_id),
                    },
                    context_ref=getattr(context_ref, "ref", str(context_ref)),
                )

        rec_id = str(uuid.uuid4())
        rec_data = {
            "id": rec_id,
            "record_id": rec_id,
            "record_type": record_type,
            "context_ref": getattr(context_ref, "ref", str(context_ref)),
            "case_id": authorized_case_id,
            "scope_id": authorized_case_id,
            "organization_id": authorized_org_id,
            "payload": payload,
            "metadata": metadata,
            "trace_id": request.trace_id,
            "task_id": request.task_id,
            "source_observation_id": source_obs_id,
            "idempotency_key": idempotency_key,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        saved_id = await self._store.save_record(rec_data)

        return self._success(
            request,
            {
                "record_id": saved_id,
                "record_type": record_type,
                "status": "active",
                "duplicate": False,
                "context_ref": getattr(context_ref, "ref", str(context_ref)),
                "case_id": authorized_case_id,
            },
            context_ref=getattr(context_ref, "ref", str(context_ref)),
        )

    async def handle_get_record(self, request: MeshRequest) -> MeshResponse:
        """Handle capability: memory.get_record, enforcing strict context isolation."""
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        context_err = self.require_context_ref(request)
        if context_err:
            return context_err

        context_ref = request.context_ref
        if not context_ref or not (getattr(context_ref, "case_id", None) or "").strip():
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A valid context_ref with non-empty case_id is required for memory reads.",
            )

        if not (getattr(context_ref, "organization_id", None) or "").strip():
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

        rec = await self._store.get_record(
            record_id=str(record_id).strip(),
            organization_id=authorized_org_id,
            case_id=authorized_case_id,
        )

        if not rec:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                "Access denied: unauthorized context or record does not exist.",
            )

        return self._success(
            request,
            {
                "record_id": rec.get("record_id") or rec.get("id"),
                "record_type": rec.get("record_type"),
                "context_ref": rec.get("context_ref") or getattr(context_ref, "ref", str(context_ref)),
                "case_id": rec.get("case_id") or authorized_case_id,
                "organization_id": rec.get("organization_id") or authorized_org_id,
                "payload": rec.get("payload", {}),
                "metadata": rec.get("metadata", {}),
                "trace_id": rec.get("trace_id"),
                "task_id": rec.get("task_id"),
                "status": rec.get("status", "active"),
                "created_at": rec.get("created_at"),
            },
            context_ref=getattr(context_ref, "ref", str(context_ref)),
        )

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    async def _infer_record_type(self, content_str: str) -> str:
        """Infer record type via Intelligence Layer or default to 'general_fact'."""
        if self._llm_client:
            prompt = (
                "You are the Memory Engine of Ring 1 General Brain. "
                "Classify the following memory content into a single concise record_type "
                "(e.g. 'legal_article', 'case_fact', 'sales_opportunity', 'logistics_manifest', 'obligation'). "
                "Return JSON: {'record_type': str}."
            )
            res = await self._call_llm_json(prompt, content_str[:500])
            if res and isinstance(res, dict) and "record_type" in res:
                return str(res["record_type"])

        return "general_fact"
