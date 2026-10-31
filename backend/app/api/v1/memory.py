"""Memory Inspection Endpoints for Ring 1 General Brain.

Enforces strict tenant isolation and scope isolation on memory reads.
Returns sanitized 404 errors to eliminate existence oracles.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.context import BrainContext, get_brain_context
from app.ring1.models.observation import MemoryRecord
from app.schemas.ring1_api import MemoryRecordResponse

router = APIRouter()


@router.get(
    "/{id}",
    response_model=MemoryRecordResponse,
    summary="Retrieve an authorized memory object by ID",
)
def get_memory_record(
    id: UUID,
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> MemoryRecordResponse:
    """Retrieve an authorized memory object enforcing tenant and scope boundaries."""
    record = db.get(MemoryRecord, id)

    # 1. Non-existent record -> 404
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MEMORY_RECORD_NOT_FOUND", "message": f"Memory record '{id}' not found"},
        )

    # 2. Cross-tenant access -> 404 (sanitize error to prevent existence oracle)
    if record.organization_id != context.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MEMORY_RECORD_NOT_FOUND", "message": f"Memory record '{id}' not found"},
        )

    # 3. Cross-scope access -> 404 (if context has a specific scope boundary)
    if context.effective_scope_id and record.case_id:
        if record.case_id != context.effective_scope_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "MEMORY_RECORD_NOT_FOUND", "message": f"Memory record '{id}' not found"},
            )

    return MemoryRecordResponse(
        id=record.id,
        record_type=record.record_type,
        context_ref=record.context_ref,
        case_id=record.case_id,
        organization_id=record.organization_id,
        payload=record.payload,
        metadata_=record.metadata_,
        status=record.status,
        trace_id=record.trace_id,
        task_id=record.task_id,
        source_observation_id=record.source_observation_id,
        idempotency_key=record.idempotency_key,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
