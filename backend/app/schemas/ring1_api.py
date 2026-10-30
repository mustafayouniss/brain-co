"""Pydantic schemas for Ring 1 General Brain API endpoints.

Covers Brain Status, Observations, Context Resolution, Memory Inspection,
and Context-Aware Lexical Retrieval.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Brain Status
# ---------------------------------------------------------------------------

class BrainStatusResponse(BaseModel):
    """Health, capabilities, and registered domains of the General Brain."""

    status: str = "online"
    engines: list[str] = Field(
        default_factory=lambda: [
            "perception",
            "observation",
            "context",
            "memory",
            "retrieval",
            "planning",
        ]
    )
    planning_advisory: bool = True
    registered_capabilities: list[str]
    registered_domains: list[str]
    organization_id: str
    environment: str


# ---------------------------------------------------------------------------
# Observation Endpoints
# ---------------------------------------------------------------------------

class ObservationCreate(BaseModel):
    """Payload to record an observation into the General Brain."""

    event_type: str = Field(..., min_length=1, max_length=100)
    source: str = Field(..., min_length=1, max_length=100)
    actor_ref: Optional[str] = None
    case_id: Optional[str] = None
    scope_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    task_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class ObservationResponse(BaseModel):
    """Serialized observation record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: str
    event_type: str
    source: str
    actor_ref: Optional[str] = None
    case_id: Optional[str] = None
    organization_id: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = Field(default=None, alias="metadata_")
    trace_id: Optional[str] = None
    task_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    status: str
    created_at: datetime


class ObservationListResponse(BaseModel):
    """Cursor-paginated observation feed with cryptographic verification."""

    items: list[ObservationResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False
    total_count: Optional[int] = None


# ---------------------------------------------------------------------------
# Context Resolution
# ---------------------------------------------------------------------------

class ContextResolveRequest(BaseModel):
    """Request to resolve and validate execution boundaries."""

    domain_id: Optional[str] = "general"
    case_id: Optional[str] = None
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    hints: dict[str, Any] = Field(default_factory=dict)


class ContextResolveResponse(BaseModel):
    """Resolved context reference with boundary constraints and ambiguity checks."""

    context_ref_id: str
    organization_id: str
    domain_id: Optional[str] = None
    case_id: Optional[str] = None
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    resolution_status: str
    ambiguities: list[str] = Field(default_factory=list)
    scope_constraints: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Memory Record
# ---------------------------------------------------------------------------

class MemoryRecordResponse(BaseModel):
    """Authorized knowledge object from Ring 1 Memory."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    record_type: str
    context_ref: Optional[str] = None
    case_id: Optional[str] = None
    organization_id: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = Field(default=None, alias="metadata_")
    status: str
    trace_id: Optional[str] = None
    task_id: Optional[str] = None
    source_observation_id: Optional[UUID] = None
    idempotency_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Retrieval Search
# ---------------------------------------------------------------------------

class RetrievalItem(BaseModel):
    """Ranked retrieval candidate."""

    record_id: str
    record_type: str
    case_id: Optional[str] = None
    status: str
    score: float
    snippet: str
    payload: dict[str, Any] = Field(default_factory=dict)


class RetrievalSearchResponse(BaseModel):
    """Context-isolated lexical search results."""

    query: str
    items: list[RetrievalItem]
    total_found: int
    organization_id: str
    case_id: Optional[str] = None
    scope_id: Optional[str] = None
