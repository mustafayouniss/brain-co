"""Tests for Context Engine."""

import pytest

from app.ring1.contracts.capabilities import CONTEXT_RESOLVE
from app.ring1.contracts.context_ref import ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.context import ContextEngine


@pytest.mark.asyncio
async def test_context_resolve_explicit(fake_llm_service):
    engine = ContextEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        payload={
            "context_hint": {
                "organization_id": "org-main",
                "case_id": "case-456",
                "domain_id": "legal",
            }
        },
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["status"] == ResolutionStatus.EXPLICIT.value
    assert resp.payload["case_id"] == "case-456"
    assert resp.payload["organization_id"] == "org-main"
    assert resp.payload["context_ref"].startswith("ctx-")



@pytest.mark.asyncio
async def test_context_resolve_missing_case(fake_llm_service):
    engine = ContextEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        payload={
            "context_hint": {
                "organization_id": "org-main",
            }
        },
    )
    resp = await engine.handle_resolve(req)
    # When case_id is missing and cannot be resolved, reports ambiguity/needs clarification
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.payload["status"] == ResolutionStatus.AMBIGUOUS.value
    assert "case_id" in resp.payload["ambiguity_reasons"][0]


@pytest.mark.asyncio
async def test_context_empty_hints_fails(fake_llm_service):
    engine = ContextEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        payload={},
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.payload["status"] == ResolutionStatus.AMBIGUOUS.value
