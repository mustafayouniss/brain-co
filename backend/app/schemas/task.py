"""Pydantic schemas for Task queries and status reporting."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskResponse(BaseModel):
    """Sanitized, safe task representation returned to the frontend."""

    model_config = ConfigDict(from_attributes=True)

    task_id: UUID
    case_id: Optional[str] = None
    source_id: Optional[str] = None
    task_type: str
    state: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    result: Optional[dict[str, Any]] = None
    error: Optional[dict[str, Any]] = None


class DocumentUploadResponse(BaseModel):
    """Response returned upon successful document upload and task dispatch."""

    task_id: UUID
    case_id: str
    source_id: UUID
    filename: str
    state: str
    message: str = "Document accepted for processing"
