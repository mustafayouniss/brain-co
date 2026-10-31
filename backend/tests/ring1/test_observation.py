"""Tests for Observation Engine."""

import pytest

from app.ring1.contracts.capabilities import OBSERVATION_RECORD_EVENT
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.observation import ObservationEngine


@pytest.mark.asyncio
async def test_observation_record_event_in_memory(fake_llm_service):
    engine = ObservationEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        payload={
            "event_type": "document.uploaded",
            "source": "api_gateway",
            "payload": {"filename": "contract.pdf", "size": 1024},
            "idempotency_key": "doc-upload-key-1",
        },
    )
    resp = await engine.handle_record_event(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["event_type"] == "document.uploaded"
    assert resp.payload["duplicate"] is False
    assert resp.payload["follow_up_required"] is True


@pytest.mark.asyncio
async def test_observation_idempotent_duplicate(fake_llm_service):
    engine = ObservationEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        payload={
            "event_type": "heartbeat",
            "source": "health_check",
            "payload": {"ping": "pong"},
            "idempotency_key": "heartbeat-unique-123",
        },
    )
    # First write
    resp1 = await engine.handle_record_event(req)
    assert resp1.status == ResultStatus.SUCCESS
    assert resp1.payload["duplicate"] is False
    assert resp1.payload["follow_up_required"] is False

    # Second write with same idempotency key
    resp2 = await engine.handle_record_event(req)
    assert resp2.status == ResultStatus.SUCCESS
    assert resp2.payload["duplicate"] is True
    assert resp2.payload["observation_id"] == resp1.payload["observation_id"]


@pytest.mark.asyncio
async def test_observation_missing_event_type(fake_llm_service):
    engine = ObservationEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        payload={"source": "api"},
    )
    resp = await engine.handle_record_event(req)
    assert resp.status == ResultStatus.INVALID_REQUEST
    assert resp.errors[0].code == EngineErrorCode.INVALID_PAYLOAD.value
