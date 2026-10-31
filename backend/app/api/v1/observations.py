"""Observation Endpoints for Ring 1 General Brain.

Supports creating observations and querying cursor-paginated feeds with HMAC
cryptographic cursor integrity and WebSocket broadcast for real-time updates.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.audit import AuditService
from app.core.context import BrainContext, get_brain_context
from app.core.cursor import decode_and_verify_cursor, encode_cursor
from app.core.ws_manager import ws_manager
from app.ring1.models.observation import Observation
from app.schemas.ring1_api import (
    ObservationCreate,
    ObservationListResponse,
    ObservationResponse,
)

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ObservationResponse,
    summary="Submit and persist an observation event",
)
async def create_observation(
    payload: ObservationCreate,
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> ObservationResponse:
    """Persist an observation in PostgreSQL and broadcast to authorized WebSocket clients."""
    case_id = payload.case_id or payload.scope_id or context.effective_scope_id
    idempotency_key = payload.idempotency_key

    # Duplicate check if idempotency_key provided
    if idempotency_key:
        existing = (
            db.query(Observation)
            .filter(Observation.idempotency_key == idempotency_key)
            .first()
        )
        if existing:
            # Enforce tenant isolation on duplicate
            if existing.organization_id != context.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "NOT_FOUND", "message": "Observation not found"},
                )
            return ObservationResponse(
                id=existing.id,
                event_id=existing.event_id,
                event_type=existing.event_type,
                source=existing.source,
                actor_ref=existing.actor_ref,
                case_id=existing.case_id,
                organization_id=existing.organization_id,
                payload=existing.payload,
                metadata_=existing.metadata_,
                trace_id=existing.trace_id,
                task_id=existing.task_id,
                idempotency_key=existing.idempotency_key,
                status=existing.status,
                created_at=existing.created_at,
            )

    obs_id = uuid.uuid4()
    obs = Observation(
        id=obs_id,
        event_id=str(obs_id),
        event_type=payload.event_type,
        source=payload.source,
        actor_ref=payload.actor_ref or context.user_id,
        case_id=case_id,
        organization_id=context.organization_id,
        payload=payload.payload,
        metadata_=payload.metadata,
        trace_id=payload.trace_id or context.correlation_id,
        task_id=payload.task_id or context.task_id,
        idempotency_key=idempotency_key,
        status="recorded",
    )
    db.add(obs)

    # Durable audit event
    AuditService.record_event(
        session=db,
        organization_id=context.organization_id,
        engine_name="observation",
        action="record_observation",
        case_id=case_id,
        actor_ref=payload.actor_ref or context.user_id,
        payload={"event_type": payload.event_type, "source": payload.source},
        correlation_id=payload.trace_id or context.correlation_id,
    )

    db.commit()
    db.refresh(obs)

    # Real-time WebSocket notification (tenant and scope isolated)
    obs_dict = {
        "id": str(obs.id),
        "event_id": obs.event_id,
        "event_type": obs.event_type,
        "source": obs.source,
        "case_id": obs.case_id,
        "organization_id": obs.organization_id,
        "payload": obs.payload,
        "created_at": obs.created_at.isoformat() if obs.created_at else None,
    }
    await ws_manager.broadcast_observation(
        organization_id=context.organization_id,
        observation=obs_dict,
        scope_id=case_id,
    )

    return ObservationResponse(
        id=obs.id,
        event_id=obs.event_id,
        event_type=obs.event_type,
        source=obs.source,
        actor_ref=obs.actor_ref,
        case_id=obs.case_id,
        organization_id=obs.organization_id,
        payload=obs.payload,
        metadata_=obs.metadata_,
        trace_id=obs.trace_id,
        task_id=obs.task_id,
        idempotency_key=obs.idempotency_key,
        status=obs.status,
        created_at=obs.created_at,
    )


@router.get(
    "",
    response_model=ObservationListResponse,
    summary="List observations with cursor pagination and filters",
)
def list_observations(
    event_type: Optional[str] = Query(None, alias="type"),
    source: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = None,
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> ObservationListResponse:
    """Retrieve an authenticated, cursor-paginated feed of observations."""
    filter_dict: dict[str, Any] = {}
    if event_type:
        filter_dict["event_type"] = event_type
    if source:
        filter_dict["source"] = source

    cursor_tuple = None
    if cursor:
        cursor_tuple = decode_and_verify_cursor(
            cursor_str=cursor,
            expected_org_id=context.organization_id,
            expected_case_id=context.effective_scope_id,
            current_filters=filter_dict,
        )

    query = db.query(Observation).filter(
        Observation.organization_id == context.organization_id
    )
    if context.effective_scope_id:
        query = query.filter(Observation.case_id == context.effective_scope_id)

    if event_type:
        query = query.filter(Observation.event_type == event_type)
    if source:
        query = query.filter(Observation.source == source)

    if cursor_tuple:
        cursor_created_at, cursor_id = cursor_tuple
        query = query.filter(
            or_(
                Observation.created_at < cursor_created_at,
                and_(
                    Observation.created_at == cursor_created_at,
                    Observation.id < cursor_id,
                ),
            )
        )

    query = query.order_by(Observation.created_at.desc(), Observation.id.desc())
    records = query.limit(limit + 1).all()

    has_more = len(records) > limit
    if has_more:
        records = records[:limit]

    next_cursor = None
    if has_more and records:
        last = records[-1]
        next_cursor = encode_cursor(
            organization_id=context.organization_id,
            case_id=context.effective_scope_id,
            current_filters=filter_dict,
            sort_order="created_at_desc_id_desc",
            created_at=last.created_at,
            row_id=last.id,
        )

    items = [
        ObservationResponse(
            id=r.id,
            event_id=r.event_id,
            event_type=r.event_type,
            source=r.source,
            actor_ref=r.actor_ref,
            case_id=r.case_id,
            organization_id=r.organization_id,
            payload=r.payload,
            metadata_=r.metadata_,
            trace_id=r.trace_id,
            task_id=r.task_id,
            idempotency_key=r.idempotency_key,
            status=r.status,
            created_at=r.created_at,
        )
        for r in records
    ]

    return ObservationListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
    )
