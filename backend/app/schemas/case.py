"""Pydantic schemas for Case management in Ring 1."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CaseCreate(BaseModel):
    """Payload to create a new Case."""

    case_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable unique case identifier (e.g. CASE-2026-001)",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Descriptive title of the legal matter",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Optional case summary or background",
    )


class CaseUpdate(BaseModel):
    """Payload to update an existing Case."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[str] = Field(default=None, pattern="^(active|in_progress|resolved|archived)$")


class CaseResponse(BaseModel):
    """Case response entity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_number: str
    title: str
    description: Optional[str] = None
    organization_id: str
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
