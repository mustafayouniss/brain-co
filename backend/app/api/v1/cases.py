"""Case Management & Case Document Processing Endpoints.

All endpoints strictly derive organization identity from BrainContext (D-004)
and enforce case-level isolation across cases, documents, tasks, and memory.
"""

from __future__ import annotations

import json
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.context import BrainContext, get_brain_context
from app.db.session import SessionLocal
from app.models.case import Case
from app.models.source import Source
from app.models.task import Task, TaskState
from app.ring1.models.observation import MemoryRecord
from app.schemas.case import CaseCreate, CaseResponse
from app.schemas.task import DocumentUploadResponse, TaskResponse
from app.services.case_service import CaseAlreadyExistsError, CaseService
from app.services.document_processing_service import (
    DocumentProcessingService,
    DocumentValidationError,
)

router = APIRouter()


def _run_worker_in_background(task_id: UUID) -> None:
    """Background worker runner triggered asynchronously by FastAPI."""
    db = SessionLocal()
    try:
        DocumentProcessingService.process_task_worker(session=db, task_id=task_id)
    finally:
        db.close()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CaseResponse,
    summary="Create a new legal Case",
)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> CaseResponse:
    """Create a new case bound to the authenticated organization."""
    user_uuid = None
    if context.user_id:
        try:
            user_uuid = UUID(context.user_id)
        except Exception:
            user_uuid = None

    try:
        new_case = CaseService.create_case(
            session=db,
            organization_id=context.organization_id,
            case_number=payload.case_number,
            title=payload.title,
            description=payload.description,
            created_by=user_uuid,
        )
        db.commit()
        db.refresh(new_case)
        return CaseResponse.model_validate(new_case)
    except CaseAlreadyExistsError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "CASE_ALREADY_EXISTS", "message": str(exc)},
        )


@router.get(
    "",
    response_model=list[CaseResponse],
    summary="List Cases for the authenticated Organization",
)
def list_cases(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> list[CaseResponse]:
    """Retrieve cases strictly scoped to the authenticated organization."""
    cases = CaseService.list_cases(
        session=db,
        organization_id=context.organization_id,
        limit=limit,
        offset=offset,
        status_filter=status_filter,
    )
    return [CaseResponse.model_validate(c) for c in cases]


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Retrieve Case details by ID",
)
def get_case(
    case_id: UUID,
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> CaseResponse:
    """Retrieve case details enforcing organization ownership."""
    c = CaseService.get_case(
        session=db,
        organization_id=context.organization_id,
        case_id=case_id,
    )
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found in this organization"},
        )
    return CaseResponse.model_validate(c)


@router.post(
    "/{case_id}/documents",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DocumentUploadResponse,
    summary="Upload PDF to Case and trigger durable background processing",
)
async def upload_case_document(
    case_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF document file"),
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> DocumentUploadResponse:
    """Upload a real PDF, register Source, create durable Task+Outbox, and dispatch worker."""
    # Verify case ownership
    c = CaseService.get_case(session=db, organization_id=context.organization_id, case_id=case_id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found in this organization"},
        )

    try:
        source, task = await DocumentProcessingService.create_document_task(
            session=db,
            case=c,
            file=file,
            context=context,
        )
        db.commit()

        # Enqueue background worker processing
        background_tasks.add_task(_run_worker_in_background, task.id)

        return DocumentUploadResponse(
            task_id=task.id,
            case_id=str(c.id),
            source_id=source.id,
            filename=source.original_filename,
            state=task.state,
            message="Document accepted and processing task dispatched",
        )
    except DocumentValidationError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_DOCUMENT", "message": str(exc)},
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "UPLOAD_FAILED", "message": f"Failed to ingest document: {str(exc)}"},
        )


@router.get(
    "/{case_id}/documents",
    summary="List uploaded documents for a Case",
)
def list_case_documents(
    case_id: UUID,
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> list[dict]:
    """List all source documents belonging to the specified case."""
    c = CaseService.get_case(session=db, organization_id=context.organization_id, case_id=case_id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found in this organization"},
        )

    sources = (
        db.query(Source)
        .filter(
            Source.case_id == str(case_id),
            Source.organization_id == context.organization_id,
        )
        .order_by(Source.created_at.desc())
        .all()
    )

    return [
        {
            "id": str(s.id),
            "original_filename": s.original_filename,
            "size_bytes": s.size_bytes,
            "content_type": s.content_type,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sources
    ]


@router.get(
    "/{case_id}/tasks",
    response_model=list[TaskResponse],
    summary="List all processing tasks for a Case",
)
def list_case_tasks(
    case_id: UUID,
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> list[TaskResponse]:
    """Retrieve all tasks created for the specified case."""
    c = CaseService.get_case(session=db, organization_id=context.organization_id, case_id=case_id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found in this organization"},
        )

    tasks = (
        db.query(Task)
        .filter(
            Task.case_id == str(case_id),
            Task.organization_id == context.organization_id,
        )
        .order_by(Task.created_at.desc())
        .all()
    )

    return [
        TaskResponse(
            task_id=t.id,
            case_id=t.case_id,
            source_id=(t.payload or {}).get("source_id"),
            task_type=t.task_type,
            state=t.state,
            created_at=t.created_at,
            started_at=t.updated_at if t.state in [TaskState.RUNNING.value, TaskState.SUCCEEDED.value, TaskState.FAILED.value] else None,
            completed_at=t.updated_at if t.state in [TaskState.SUCCEEDED.value, TaskState.FAILED.value] else None,
            retry_count=t.retry_count,
            result=t.result,
            error=t.error_details,
        )
        for t in tasks
    ]


@router.get(
    "/{case_id}/knowledge",
    summary="Query persisted knowledge records for a Case",
)
def get_case_knowledge(
    case_id: UUID,
    query: str = Query(default="", description="Optional search filter"),
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> dict:
    """Retrieve persisted memory records for a case strictly enforcing case isolation."""
    c = CaseService.get_case(session=db, organization_id=context.organization_id, case_id=case_id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CASE_NOT_FOUND", "message": f"Case '{case_id}' not found in this organization"},
        )

    stmt = (
        sa.select(MemoryRecord)
        .where(
            MemoryRecord.organization_id == context.organization_id,
            MemoryRecord.case_id == str(case_id),
        )
        .order_by(MemoryRecord.created_at.desc())
    )
    records = db.scalars(stmt).all()

    filtered = []
    for r in records:
        if query and query.lower() not in json.dumps(r.payload).lower():
            continue
        filtered.append({
            "record_id": str(r.id),
            "record_type": r.record_type,
            "status": r.status,  # candidate or validated
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "payload": r.payload,
            "case_id": r.case_id,
            "organization_id": r.organization_id,
            "provenance": r.metadata_,
        })

    return {
        "case_id": str(case_id),
        "organization_id": context.organization_id,
        "total": len(filtered),
        "records": filtered,
    }
