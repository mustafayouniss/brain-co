"""Adversarial and regression tests for SEC-02: Context Engine Trust Boundaries and ENG-01: LLM Fallback Reachability.

Verifies:
1. Missing server-side organization context fails closed (client hints cannot fabricate tenant identity).
2. Client cannot override authenticated organization scope.
3. Client cannot override authoritative case scope.
4. Case validator rejects unauthorized case hints with AUTHORIZATION_DENIED.
5. Case validator admits verified case hints with EXPLICIT status.
6. Unvalidated hints without a validator are marked INFERRED, never EXPLICIT.
7. LLM resolution fallback is reachable (fixing ENG-01) and strictly cannot override server organization.
8. API endpoint POST /api/v1/context/resolve rejects forbidden scope overrides with HTTP 403.
"""

from __future__ import annotations

import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from brain.general.contracts.capabilities import CONTEXT_RESOLVE
from brain.general.contracts.context import BrainContext
from brain.general.contracts.context_ref import ContextRef, ResolutionStatus
from brain.general.contracts.envelopes import MeshRequest, ResultStatus
from brain.general.contracts.errors import EngineErrorCode
from brain.general.engines.context import ContextEngine
from ai.core.services.llm_service import LLMService
from ai.providers.fake_provider import FakeLLMProvider
from app.core.security import create_access_token, hash_password
from app.models.user import User


@pytest.fixture
def auth_headers(db_session: Session) -> dict[str, str]:
    user = User(
        email=f"tester_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Context Tester",
        hashed_password=hash_password("password123"),
        role="employee",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_context_missing_server_org_fails_closed(fake_llm_service: LLMService):
    """SEC-02: Missing server organization context must fail closed."""
    engine = ContextEngine(llm_service=fake_llm_service)

    # Caller attempts to fabricate tenant identity purely through context_hint
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=None,  # No verified server context
        payload={
            "context_hint": {
                "organization_id": "spoofed-tenant-999",
                "case_id": "case-xyz",
            }
        },
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.FAILED
    assert any(err.code == EngineErrorCode.CONTEXT_MISSING.value for err in resp.errors)


@pytest.mark.asyncio
async def test_context_client_attempted_org_override_rejected(fake_llm_service: LLMService):
    """SEC-02: Client cannot override authenticated organization scope."""
    engine = ContextEngine(llm_service=fake_llm_service)

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-legitimate"),
        payload={
            "context_hint": {
                "organization_id": "org-attacker-override",
                "case_id": "case-123",
            }
        },
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.FAILED
    assert any(err.code == EngineErrorCode.AUTHORIZATION_DENIED.value for err in resp.errors)


@pytest.mark.asyncio
async def test_context_client_attempted_case_override_rejected(fake_llm_service: LLMService):
    """SEC-02: Server-side case scope is authoritative; hints cannot override it."""
    engine = ContextEngine(llm_service=fake_llm_service)

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-main", case_id="case-authoritative-100"),
        payload={
            "context_hint": {
                "organization_id": "org-main",
                "case_id": "case-spoofed-999",  # Attempted breakout
            }
        },
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.FAILED
    assert any(err.code == EngineErrorCode.AUTHORIZATION_DENIED.value for err in resp.errors)


@pytest.mark.asyncio
async def test_context_case_validator_rejection(fake_llm_service: LLMService):
    """SEC-02: Case validator rejects unauthenticated case hints."""
    authorized_cases = {"org-alpha": {"case-allowed-1", "case-allowed-2"}}

    def mock_validator(org_id: str, case_id: str, user_id: str | None = None) -> bool:
        return case_id in authorized_cases.get(org_id, set())

    engine = ContextEngine(llm_service=fake_llm_service, case_validator=mock_validator)

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-alpha"),  # Token has org, no case
        payload={
            "context_hint": {
                "organization_id": "org-alpha",
                "case_id": "case-foreign-999",  # Unauthorized case
            }
        },
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.FAILED
    assert any(err.code == EngineErrorCode.AUTHORIZATION_DENIED.value for err in resp.errors)


@pytest.mark.asyncio
async def test_context_case_validator_success(fake_llm_service: LLMService):
    """SEC-02: Case validator admits valid case hints with EXPLICIT status."""
    authorized_cases = {"org-alpha": {"case-allowed-1", "case-allowed-2"}}

    def mock_validator(org_id: str, case_id: str, user_id: str | None = None) -> bool:
        return case_id in authorized_cases.get(org_id, set())

    engine = ContextEngine(llm_service=fake_llm_service, case_validator=mock_validator)

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-alpha"),
        payload={
            "context_hint": {
                "organization_id": "org-alpha",
                "case_id": "case-allowed-1",
            }
        },
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["case_id"] == "case-allowed-1"
    assert resp.payload["status"] == ResolutionStatus.EXPLICIT.value


@pytest.mark.asyncio
async def test_context_explicit_hint_resolution_no_validator_fails_closed(fake_llm_service: LLMService):
    """SEC-02-F01: Explicit case hint without validator FAILS CLOSED."""
    engine = ContextEngine(llm_service=fake_llm_service)  # No case_validator

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-alpha"),
        payload={
            "context_hint": {
                "organization_id": "org-alpha",
                "case_id": "case-unverified-555",
            }
        },
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.FAILED
    assert any(err.code == EngineErrorCode.AUTHORIZATION_DENIED.value for err in resp.errors)
    assert "no case validator configured" in resp.errors[0].message.lower()


@pytest.mark.asyncio
async def test_context_explicit_hint_resolution_with_valid_validator(fake_llm_service: LLMService):
    """SEC-02-F01: Explicit case hint with verifying validator resolves cleanly to EXPLICIT."""
    engine = ContextEngine(
        llm_service=fake_llm_service,
        case_validator=lambda org, case, user: case == "case-verified-555",
    )

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-alpha"),
        payload={
            "context_hint": {
                "organization_id": "org-alpha",
                "case_id": "case-verified-555",
            }
        },
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["case_id"] == "case-verified-555"
    assert resp.payload["status"] == ResolutionStatus.EXPLICIT.value


@pytest.mark.asyncio
async def test_context_llm_fallback_no_validator_fails_closed():
    """SEC-02-F01: When case is inferred by LLM but no validator is configured, unverified case is stripped."""
    provider = FakeLLMProvider()
    provider.set_custom_response(json.dumps({
        "case_id": "case-inferred-777",
        "domain_id": "commercial",
        "confidence": 0.95,
    }))
    service = LLMService(provider=provider)
    engine = ContextEngine(llm_service=service)  # No validator

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-authoritative"),
        payload={"metadata": {"contract_title": "Commercial dispute"}},
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.payload["case_id"] is None
    assert resp.payload["scope_id"] is None
    assert resp.payload["resolution_status"] == ResolutionStatus.AMBIGUOUS.value
    # Scope constraints MUST NOT contain the unverified case ID
    assert f"case_id=case-inferred-777" not in resp.payload["scope_constraints"]
    assert resp.payload["organization_id"] == "org-authoritative"


@pytest.mark.asyncio
async def test_context_llm_fallback_reachability_and_org_preservation():
    """ENG-01 & SEC-02-F01: When case is verified by validator, LLM inference resolves and preserves server org."""
    provider = FakeLLMProvider()
    provider.set_custom_response(json.dumps({
        "case_id": "case-inferred-777",
        "domain_id": "commercial",
        "organization_id": "evil-override-attempt",  # LLM attempts to return another org
        "confidence": 0.95,
    }))
    service = LLMService(provider=provider)
    engine = ContextEngine(
        llm_service=service,
        case_validator=lambda org, case, user: case == "case-inferred-777",
    )

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-authoritative"),
        payload={"metadata": {"contract_title": "Commercial dispute"}},
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["case_id"] == "case-inferred-777"
    # Organization must remain the verified server org, NOT the LLM's hallucination
    assert resp.payload["organization_id"] == "org-authoritative"


@pytest.mark.asyncio
async def test_context_llm_fallback_validator_exception_downgrades():
    """SEC-02-F01: When validator raises exception during LLM fallback, inferred case is downgraded safely."""
    provider = FakeLLMProvider()
    provider.set_custom_response(json.dumps({
        "case_id": "case-inferred-crash",
        "confidence": 0.95,
    }))
    service = LLMService(provider=provider)

    def crashing_validator(org: str, case: str, user: str | None = None) -> bool:
        raise RuntimeError("Database connection pool exhausted")

    engine = ContextEngine(llm_service=service, case_validator=crashing_validator)

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-authoritative"),
        payload={"metadata": {"note": "Dispute"}},
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.payload["case_id"] is None
    assert resp.payload["resolution_status"] == ResolutionStatus.AMBIGUOUS.value
    # Safe error message: no database pool internals exposed
    assert "Database connection pool exhausted" not in str(resp.payload.get("ambiguities", []))


@pytest.mark.asyncio
async def test_resolve_context_no_validator_fails_closed():
    """SEC-02-F01: resolve_context fails closed when client case is provided without validator."""
    engine = ContextEngine()  # No validator
    context = BrainContext(organization_id="org-beta", user_id="user-1")
    request_scope = {"case_id": "case-secret-99"}

    result = await engine.resolve_context(request_scope, context)
    assert result.error is not None
    assert result.error["code"] == "AUTHORIZATION_DENIED"
    assert "no case validator configured" in result.error["message"].lower()


@pytest.mark.asyncio
async def test_resolve_context_validator_rejection_fails_closed():
    """SEC-02-F01: resolve_context fails closed when validator returns False."""
    engine = ContextEngine(case_validator=lambda org, case, user: False)
    context = BrainContext(organization_id="org-beta", user_id="user-1")
    request_scope = {"case_id": "case-foreign-1"}

    result = await engine.resolve_context(request_scope, context)
    assert result.error is not None
    assert result.error["code"] == "AUTHORIZATION_DENIED"
    assert "Access denied to case 'case-foreign-1'" in result.error["message"]


@pytest.mark.asyncio
async def test_resolve_context_validator_exception_fails_closed_safe_error():
    """SEC-02-F01: resolve_context sanitizes errors when validator raises an exception."""
    def crashing_validator(org: str, case: str, user: str | None = None) -> bool:
        raise ConnectionRefusedError("PostgreSQL connection lost on port 5432")

    engine = ContextEngine(case_validator=crashing_validator)
    context = BrainContext(organization_id="org-beta", user_id="user-1")
    request_scope = {"case_id": "case-123"}

    result = await engine.resolve_context(request_scope, context)
    assert result.error is not None
    assert result.error["code"] == "AUTHORIZATION_DENIED"
    # Never expose internal database error details to caller
    assert "PostgreSQL" not in result.error["message"]
    assert "5432" not in result.error["message"]
    assert "authorization check failed" in result.error["message"]


@pytest.mark.asyncio
async def test_resolve_context_validator_success():
    """SEC-02-F01: resolve_context resolves EXPLICIT when validator returns True."""
    engine = ContextEngine(case_validator=lambda org, case, user: True)
    context = BrainContext(organization_id="org-beta", user_id="user-1")
    request_scope = {"case_id": "case-authorized-1"}

    result = await engine.resolve_context(request_scope, context)
    assert result.error is None
    assert result.data["case_id"] == "case-authorized-1"
    assert result.data["status"] == "explicit"
    assert result.data["resolution_status"] == "explicit"


@pytest.mark.asyncio
async def test_resolve_context_rejects_empty_or_whitespace_case():
    """SEC-02-F01: resolve_context rejects empty or whitespace-only scope strings."""
    engine = ContextEngine(case_validator=lambda org, case, user: True)
    context = BrainContext(organization_id="org-beta", user_id="user-1")
    request_scope = {"case_id": "   "}

    result = await engine.resolve_context(request_scope, context)
    assert result.error is not None
    assert result.error["code"] == "INVALID_SCOPE"


@pytest.mark.asyncio
async def test_handle_resolve_rejects_empty_whitespace_hint_case(fake_llm_service: LLMService):
    """SEC-02-F01: handle_resolve rejects whitespace-only hint_case."""
    engine = ContextEngine(llm_service=fake_llm_service, case_validator=lambda org, case, user: True)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-alpha"),
        payload={"context_hint": {"case_id": "   "}},
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.FAILED
    assert any(err.code == EngineErrorCode.INVALID_PAYLOAD.value for err in resp.errors)


@pytest.mark.asyncio
async def test_handle_resolve_validator_exception_fails_closed_safe_error(fake_llm_service: LLMService):
    """SEC-02-F01: handle_resolve logs validator exceptions and returns safe generic error."""
    def crash_val(org: str, case: str, user: str | None = None) -> bool:
        raise ValueError("Sensitive internal secret in database query: SELECT * FROM cases")

    engine = ContextEngine(llm_service=fake_llm_service, case_validator=crash_val)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-alpha"),
        payload={"context_hint": {"case_id": "case-999"}},
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.FAILED
    assert any(err.code == EngineErrorCode.AUTHORIZATION_DENIED.value for err in resp.errors)
    # The sensitive internal secret must NOT be in the response
    assert "SELECT * FROM cases" not in resp.errors[0].message
    assert "authorization check failed" in resp.errors[0].message


@pytest.mark.asyncio
async def test_server_case_trusted_provenance_bypasses_validator_only_when_internal_and_resolved(fake_llm_service: LLMService):
    """SEC-02-F01: Server case in ContextRef cannot bypass validator when sent by client or unresolved."""
    engine = ContextEngine(llm_service=fake_llm_service)  # No validator configured

    # 1. Client spoofing attempt: external client claims pre-resolved ContextRef
    spoofed_req = MeshRequest(
        sender_engine="client",  # External client
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(
            organization_id="org-alpha",
            case_id="case-spoofed-1",
            resolution_status=ResolutionStatus.EXPLICIT,
            scope_constraints=["case_id=case-spoofed-1"],
        ),
        payload={"context_hint": {"case_id": "case-spoofed-1"}},
    )
    resp = await engine.handle_resolve(spoofed_req)
    assert resp.status == ResultStatus.FAILED
    assert any(err.code == EngineErrorCode.AUTHORIZATION_DENIED.value for err in resp.errors)

    # 2. Genuine internal engine delegation carrying already-resolved context:
    trusted_req = MeshRequest(
        sender_engine="observation",  # Internal mesh engine
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(
            context_ref_id="ctx-already-authorized",
            organization_id="org-alpha",
            case_id="case-trusted-1",
            resolution_status=ResolutionStatus.EXPLICIT,
            scope_constraints=["case_id=case-trusted-1", "organization_id=org-alpha"],
        ),
        payload={},
    )
    resp_trusted = await engine.handle_resolve(trusted_req)
    assert resp_trusted.status == ResultStatus.SUCCESS
    assert resp_trusted.payload["case_id"] == "case-trusted-1"
    assert resp_trusted.payload["status"] == ResolutionStatus.EXPLICIT.value


@pytest.mark.asyncio
async def test_generic_domain_scope_requires_validation():
    """SEC-02-F01 (Adjustment 3): An arbitrary generic domain scope cannot become authorized without validation."""
    engine = ContextEngine()  # No validator
    context = BrainContext(organization_id="org-fleet", domain_id="logistics")
    request_scope = {"domain_id": "logistics", "scope_id": "voyage-pacific-992"}

    result = await engine.resolve_context(request_scope, context)
    assert result.error is not None
    assert result.error["code"] == "AUTHORIZATION_DENIED"


@pytest.mark.asyncio
async def test_unverified_case_never_reaches_authorized_scope(fake_llm_service: LLMService):
    """SEC-02-F01 (Adjustment 1 & 6): Unverified case cannot establish an authorized ContextRef."""
    engine = ContextEngine(llm_service=fake_llm_service)  # No validator

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        context_ref=ContextRef(organization_id="org-isolated"),
        payload={"context_hint": {"case_id": "case-leak-attempt"}},
    )
    resp = await engine.handle_resolve(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.payload == {}
    assert any(err.code == EngineErrorCode.AUTHORIZATION_DENIED.value for err in resp.errors)
    # Ensure unverified case was never authorized in payload
    assert "case_id" not in resp.payload


def test_api_v1_context_resolve_rejects_case_override(client: TestClient, auth_headers: dict[str, str]):
    """SEC-02: API layer rejects client attempt to override server case scope."""
    # When token or context is scoped to case-legit, body proposing case-evil is rejected with HTTP 403
    response = client.post(
        "/api/v1/context/resolve",
        json={
            "case_id": "case-evil-override",
            "domain_id": "legal",
        },
        headers={**auth_headers, "X-Case-ID": "case-authoritative-scope"},
    )
    assert response.status_code == 403
    err_body = response.json()
    msg = err_body.get("detail") or err_body.get("error", {}).get("message", "")
    assert "override" in msg.lower()
