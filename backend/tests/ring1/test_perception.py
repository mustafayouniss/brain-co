"""Tests for Perception Engine."""

import json
import pytest

from app.ring1.contracts.capabilities import PERCEPTION_STRUCTURE_INPUT
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.perception import PerceptionEngine


@pytest.mark.asyncio
async def test_perception_parse_json_deterministic(fake_llm_service):
    engine = PerceptionEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={"raw_content": '{"key": "value", "count": 42}', "input_type": "json"},
    )
    resp = await engine.handle_structure_input(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["parsed_content"] == {"key": "value", "count": 42}
    assert resp.payload["extracted_metadata"]["key_count"] == 2


@pytest.mark.asyncio
async def test_perception_parse_text_deterministic(fake_llm_service):
    engine = PerceptionEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={"raw_content": "This is a simple legal brief document.\nWith two lines."},
    )
    resp = await engine.handle_structure_input(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["detected_type"] == "text"
    assert resp.payload["extracted_metadata"]["word_count"] > 0
    assert resp.payload["extracted_metadata"]["line_count"] == 2


@pytest.mark.asyncio
async def test_perception_system_event(fake_llm_service):
    engine = PerceptionEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={
            "raw_content": json.dumps({"event": "case_created", "case_id": "case-99"}),
            "input_type": "system_event",
        },
    )
    resp = await engine.handle_structure_input(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["detected_type"] == "system_event"
    assert resp.payload["parsed_content"]["event"] == "case_created"


@pytest.mark.asyncio
async def test_perception_missing_raw_content(fake_llm_service):
    engine = PerceptionEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={},
    )
    resp = await engine.handle_structure_input(req)
    assert resp.status == ResultStatus.INVALID_REQUEST
    assert resp.errors[0].code == EngineErrorCode.INVALID_PAYLOAD.value


@pytest.mark.asyncio
async def test_perception_unsupported_type(fake_llm_service):
    engine = PerceptionEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={"raw_content": "data", "input_type": "binary_executable"},
    )
    resp = await engine.handle_structure_input(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.UNSUPPORTED_INPUT_TYPE.value
