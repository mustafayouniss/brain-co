"""Task Status & Forensic Inspection Endpoints.

Provides authenticated task inspection strictly enforcing organization ownership.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.context import BrainContext, get_brain_context
from app.models.task import Task, TaskState
from app.schemas.task import TaskResponse

router = APIRouter()


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get Task status and details by ID",
)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> TaskResponse:
    """Retrieve sanitized task status enforcing organization boundary."""
    task = db.get(Task, task_id)
    if not task or task.organization_id != context.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TASK_NOT_FOUND", "message": f"Task '{task_id}' not found in this organization"},
        )

    return TaskResponse(
        task_id=task.id,
        case_id=task.case_id,
        source_id=(task.payload or {}).get("source_id"),
        task_type=task.task_type,
        state=task.state,
        created_at=task.created_at,
        started_at=task.updated_at if task.state in [TaskState.RUNNING.value, TaskState.SUCCEEDED.value, TaskState.FAILED.value] else None,
        completed_at=task.updated_at if task.state in [TaskState.SUCCEEDED.value, TaskState.FAILED.value] else None,
        retry_count=task.retry_count,
        result=task.result,
        error=task.error_details,
    )
