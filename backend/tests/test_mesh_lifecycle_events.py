"""Unit and integration tests for MeshEventService, canonical lifecycle events, and dual delivery."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch
import uuid
import pytest
from sqlalchemy.orm import Session

from app.core.ws_manager import ws_manager
from app.models.case import Case
from app.models.mesh_event import MeshEventRecord
from app.models.organization import Organization
from app.services.mesh_event_service import (
    MeshEventService,
    MeshLifecycleEventType,
)


@pytest.fixture
def test_org_and_case(db_session: Session):
    org_id = f"org-mesh-{uuid.uuid4().hex[:6]}"
    case_num = f"CASE-MESH-{uuid.uuid4().hex[:4]}"
    org = Organization(id=org_id, name="Mesh Test Org", slug=org_id, domain="legal")
    case = Case(
        id=uuid.uuid4(),
        case_number=case_num,
        title="Maritime Dispute",
        organization_id=org_id,
        status="open",
    )
    db_session.add_all([org, case])
    db_session.commit()
    return org_id, case_num


@pytest.mark.asyncio
async def test_canonical_lifecycle_event_types():
    """Verify all 12 canonical lifecycle event types are defined and unique."""
    expected = [
        "task_created",
        "task_dispatched",
        "task_received",
        "context_retrieved",
        "tool_invoked",
        "tool_completed",
        "handoff_evaluated",
        "observation_persisted",
        "memory_persisted",
        "task_completed",
        "task_failed",
        "task_retry",
    ]
    for ev in expected:
        attr = ev.upper()
        assert hasattr(MeshLifecycleEventType, attr)
        assert getattr(MeshLifecycleEventType, attr) == ev


@pytest.mark.asyncio
async def test_mesh_event_service_record_and_dual_delivery(db_session: Session, test_org_and_case):
    """Verify event formatting, database persistence into mesh_events, and ws_manager broadcast."""
    org_id, case_num = test_org_and_case
    run_id = uuid.uuid4()

    mock_broadcast = AsyncMock(return_value=1)
    with patch.object(ws_manager, "broadcast_event", mock_broadcast):
        event_dict = await MeshEventService.record_and_broadcast(
            session=db_session,
            run_id=run_id,
            sequence_number=1,
            organization_id=org_id,
            case_id=case_num,
            source_engine="client",
            destination_engine="context",
            capability="context.resolve",
            event_type=MeshLifecycleEventType.TASK_DISPATCHED,
            status="running",
            duration_ms=45,
            plan_version=1,
            payload={"test_key": "val_123"},
            broadcast=True,
        )

        assert event_dict["organization_id"] == org_id
        assert event_dict["case_id"] == case_num
        assert event_dict["sequence_number"] == 1
        assert event_dict["event_type"] == MeshLifecycleEventType.TASK_DISPATCHED
        assert event_dict["status"] == "running"
        assert event_dict["duration_ms"] == 45
        assert event_dict["payload"] == {"test_key": "val_123"}
        assert "timestamp" in event_dict

        # Verify ws_manager dual broadcast was called with exact boundary filters
        mock_broadcast.assert_awaited_once_with(
            organization_id=org_id,
            event_payload=event_dict,
            case_id=case_num,
        )

        # Verify database record was added
        db_record = db_session.query(MeshEventRecord).filter(
            MeshEventRecord.organization_id == org_id,
            MeshEventRecord.sequence_number == 1,
        ).first()
        assert db_record is not None
        assert db_record.event_type == MeshLifecycleEventType.TASK_DISPATCHED
        assert db_record.capability == "context.resolve"
        assert db_record.payload == {"test_key": "val_123"}
