"""Ring 1 Live Test & Observability API Endpoints.

Provides developer and administrative endpoints to trigger real-time, reproducible
scenarios across all six Ring 1 engines with Server-Sent Events (SSE) streaming
and deep execution inspection.
"""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_test_operator_user
from app.models.user import User
from app.ring1.contracts.capabilities import ALL_CAPABILITIES
from app.ring1.service import Ring1TestRunner, test_run_registry

router = APIRouter()


class TestRunRequest(BaseModel):
    mode: Literal["e2e", "force_failure", "custom_prompt"] = Field(
        default="e2e",
        description="Execution mode: e2e (all 6 engines), force_failure (controlled replan), or custom_prompt",
    )
    custom_prompt: str | None = Field(
        default=None,
        description="Optional custom text prompt for custom_prompt execution mode",
    )
    stream: bool = Field(
        default=True,
        description="Whether to stream real-time events via Server-Sent Events (SSE)",
    )


@router.post("/test-run", summary="Execute Ring 1 Live Integration Test")
async def execute_ring1_test(
    request: TestRunRequest,
    db: Session = Depends(get_db),
    _user: User | None = Depends(get_test_operator_user),
):
    """Execute live scenario across the six Ring 1 engines.

    Streams structured execution events as SSE if stream=True,
    or returns complete run result as JSON if stream=False.
    """
    runner = Ring1TestRunner(db_session=db)

    if request.stream:
        async def sse_event_generator():
            try:
                async for event in runner.execute(
                    mode=request.mode,
                    custom_prompt=request.custom_prompt,
                ):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as exc:
                err_payload = {
                    "event_type": "error",
                    "status": "failed",
                    "error": str(exc),
                }
                yield f"data: {json.dumps(err_payload)}\n\n"

        return StreamingResponse(
            sse_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming fallback
    events = []
    async for event in runner.execute(mode=request.mode, custom_prompt=request.custom_prompt):
        events.append(event)

    summary = events[-1]["details"] if events else {}
    return {
        "status": "completed",
        "run_id": summary.get("run_id"),
        "events": events,
        "summary": summary,
    }


@router.get("/test-runs/{run_id}", summary="Get Stored Test Run Details")
def get_test_run(
    run_id: str,
    _user: User | None = Depends(get_test_operator_user),
):
    """Retrieve full trace, plan versions, and graph data for a completed run."""
    run = test_run_registry.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run '{run_id}' not found in registry",
        )
    return run


@router.get("/test-runs", summary="List Recent Test Runs")
def list_test_runs(
    limit: int = Query(default=15, ge=1, le=50),
    _user: User | None = Depends(get_test_operator_user),
):
    """List recent Ring 1 live test runs."""
    return test_run_registry.list_runs(limit=limit)


@router.get("/capabilities", summary="List Ring 1 Capabilities & Engine Status")
def get_capabilities(
    _user: User | None = Depends(get_test_operator_user),
):
    """Return all registered Ring 1 capabilities and supported engines."""
    return {
        "status": "ready",
        "protocol_version": "1.0",
        "engines": [
            {"name": "perception", "status": "active"},
            {"name": "observation", "status": "active"},
            {"name": "context", "status": "active"},
            {"name": "memory", "status": "active"},
            {"name": "retrieval", "status": "active"},
            {"name": "planning", "status": "active"},
        ],
        "capabilities": sorted(list(ALL_CAPABILITIES)),
    }


MAX_PDF_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB limit


@router.post("/upload-pdf", summary="Upload and Ingest Real PDF into Ring 1 Knowledge Pipeline")
async def upload_pdf(
    file: UploadFile = File(..., description="Real PDF file to ingest"),
    organization_id: str = Form(..., description="Target organization ID"),
    case_id: str = Form(..., description="Target case ID"),
    mode: Literal["normal", "failure_recovery"] = Form("normal", description="Execution mode: normal or failure_recovery"),
    stream: bool = Form(True, description="Whether to stream real-time events via Server-Sent Events (SSE)"),
    db: Session = Depends(get_db),
    _user: User | None = Depends(get_test_operator_user),
):
    """Process an uploaded PDF through the real Ring 1 Peer-to-Peer Capability Mesh.

    Pipeline sequence:
    1. Read real PDF bytes (enforce 20MB limit and signature check).
    2. PDFExtractor extracts text page by page with exact page numbers.
    3. StructuredKnowledgeExtractor extracts facts, dates, entities, and Egyptian legal obligations.
    4. PerceptionEngine structures the input.
    5. ObservationEngine durably records the ingestion event into PostgreSQL (with SHA-256 idempotency).
    6. ContextEngine establishes case authorization prerequisites.
    7. PlanningEngine generates capability steps.
    8. PlanStepExecutor executes steps (persisting to PostgreSQL ring1_memory_records).
    9. Separate verification query confirms stored facts can be retrieved.
    10. Complete scorecard and structured knowledge returned.
    """
    clean_org_id = organization_id.strip()
    clean_case_id = case_id.strip()
    if not clean_org_id or not clean_case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id and case_id are required non-empty parameters.",
        )

    # Sanitize filename
    raw_filename = file.filename or "uploaded_document.pdf"
    safe_filename = raw_filename.replace("\\", "/").split("/")[-1].strip() or "document.pdf"

    # Read bytes safely with bounded limit
    pdf_bytes = await file.read(MAX_PDF_SIZE_BYTES + 1)
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_PDF_SIZE_BYTES // (1024 * 1024)}MB",
        )

    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file signature: File must be a valid PDF starting with %PDF-",
        )

    runner = Ring1TestRunner(db_session=db)

    if stream:
        async def sse_event_generator():
            try:
                async for event in runner.execute_pdf(
                    pdf_bytes=pdf_bytes,
                    filename=safe_filename,
                    organization_id=clean_org_id,
                    case_id=clean_case_id,
                    mode=mode,
                ):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as exc:
                err_payload = {
                    "event_type": "error",
                    "status": "failed",
                    "error": str(exc),
                }
                yield f"data: {json.dumps(err_payload)}\n\n"

        return StreamingResponse(
            sse_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming fallback
    events = []
    async for event in runner.execute_pdf(
        pdf_bytes=pdf_bytes,
        filename=safe_filename,
        organization_id=clean_org_id,
        case_id=clean_case_id,
        mode=mode,
    ):
        events.append(event)

    summary = events[-1]["details"] if events else {}
    return {
        "status": summary.get("status", "completed"),
        "run_id": summary.get("run_id"),
        "events": events,
        "summary": summary,
    }


@router.get("/knowledge", summary="Query Persisted Knowledge Records for Case")
def get_case_knowledge(
    organization_id: str = Query(..., description="Target Organization ID"),
    case_id: str = Query(..., description="Target Case ID"),
    query: str = Query(default="", description="Optional search filter"),
    db: Session = Depends(get_db),
    _user: User | None = Depends(get_test_operator_user),
):
    """Query persisted knowledge records directly from PostgreSQL ring1_memory_records table.

    Enforces case and organization context isolation server-side.
    """
    clean_org_id = organization_id.strip()
    clean_case_id = case_id.strip()
    if not clean_org_id or not clean_case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id and case_id are required non-empty parameters.",
        )

    runner = Ring1TestRunner(db_session=db)
    records = runner.query_saved_knowledge(
        organization_id=clean_org_id,
        case_id=clean_case_id,
        query=query,
    )
    return {
        "organization_id": clean_org_id,
        "case_id": clean_case_id,
        "total": len(records),
        "records": records,
    }
