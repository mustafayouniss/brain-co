"""End-to-End Tests for Ring 1 Real PDF Ingestion & Knowledge Persistence.

Verifies:
1. Real PDF binary creation and extraction.
2. Full normal pipeline:
   PDF -> Extraction -> Perception -> Observation (PostgreSQL) -> Context ->
   Planning -> PlanStepExecutor -> Basic Memory (PostgreSQL) ->
   Retrieval Verification -> Final Scorecard.
3. Live HTTP API execution via FastAPI TestClient (both non-streaming and SSE).
4. Failure & Recovery mode:
   Step 1 context resolution failure -> prerequisite blocking of downstream steps ->
   evidence-based replanning -> recovery step execution -> unblocking -> successful verification.
5. Strict cross-case context isolation (cannot retrieve stored facts using wrong case_id).
6. Multi-service persistence verification: facts durably survive in PostgreSQL across fresh runner instances.
"""

from __future__ import annotations

import io
import json
import uuid
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.ring1.models.observation import MemoryRecord, Observation
from app.ring1.service import Ring1TestRunner, test_run_registry


def _create_sample_contract_pdf() -> bytes:
    """Generate a multi-page valid PDF contract with known facts, dates, and articles."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    # Page 1
    c.drawString(72, 750, "COMMERCIAL CONSULTING AGREEMENT")
    c.drawString(72, 720, "Dated: 2026-10-15")
    c.drawString(72, 690, "Party A: Apex Global Holdings LLC (Principal)")
    c.drawString(72, 660, "Party B: Cairo Legal Consultants SAE (Advisor)")
    c.drawString(72, 630, "Article 147: The contract makes the law of the parties.")
    c.drawString(72, 600, "Scope: Providing advisory services for regional compliance.")
    c.showPage()

    # Page 2
    c.drawString(72, 750, "FINANCIAL TERMS AND CONFIDENTIALITY")
    c.drawString(72, 720, "Retainer Fee: USD 50,000 payable upon signing.")
    c.drawString(72, 690, "Payment Date: Due on 2026-11-01.")
    c.drawString(72, 660, "Obligation: Party B shall maintain strict confidentiality regarding all proprietary methods.")
    c.drawString(72, 630, "Governing Law: Subject to the Egyptian Civil Code Article 147 and related statutes.")
    c.showPage()

    c.save()
    buf.seek(0)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_pdf_e2e_normal_pipeline(db_session):
    """Test full normal PDF ingestion pipeline through Ring1TestRunner directly."""
    runner = Ring1TestRunner(db_session=db_session)
    pdf_bytes = _create_sample_contract_pdf()
    org_id = f"org-test-{uuid.uuid4().hex[:6]}"
    case_id = f"case-pdf-{uuid.uuid4().hex[:6]}"

    events = []
    async for evt in runner.execute_pdf(
        pdf_bytes=pdf_bytes,
        filename="contract_agreement.pdf",
        organization_id=org_id,
        case_id=case_id,
        mode="normal",
    ):
        events.append(evt)

    assert len(events) > 5

    # 1. Verify Extraction Event
    ext_evts = [e for e in events if e["event_type"] == "extraction_completed"]
    assert len(ext_evts) == 1
    assert ext_evts[0]["details"]["pages_count"] == 2
    assert ext_evts[0]["details"]["requires_ocr"] is False

    # 2. Verify Structured Knowledge Extracted
    struct_evts = [e for e in events if e["event_type"] == "knowledge_structured"]
    assert len(struct_evts) == 1
    assert struct_evts[0]["details"]["facts_count"] > 0
    assert struct_evts[0]["details"]["entities_count"] > 0

    # 3. Verify Observation Persisted in PostgreSQL
    obs_evts = [e for e in events if e["event_type"] == "observation_persisted"]
    assert len(obs_evts) == 1
    obs_id = obs_evts[0]["details"]["observation_id"]
    assert obs_id is not None

    db_obs = db_session.get(Observation, obs_id)
    assert db_obs is not None
    assert db_obs.organization_id == org_id
    assert db_obs.case_id == case_id
    assert db_obs.event_type == "pdf_document_ingested"

    # 4. Verify Context Resolved
    ctx_evts = [e for e in events if e["event_type"] == "context_resolved"]
    assert len(ctx_evts) >= 1

    # 5. Verify Plan Created
    plan_evts = [e for e in events if e["event_type"] == "plan_created"]
    assert len(plan_evts) == 1
    assert plan_evts[0]["details"]["steps_count"] == 3

    # 6. Verify Step Executions Completed
    completed_steps = [e for e in events if e["event_type"] == "step_completed"]
    assert len(completed_steps) >= 3

    # 7. Verify Facts Persisted in PostgreSQL ring1_memory_records
    mem_records = runner.query_saved_knowledge(organization_id=org_id, case_id=case_id)
    assert len(mem_records) >= 1
    saved_payload = mem_records[0]["payload"]
    assert saved_payload["filename"] == "contract_agreement.pdf"
    assert len(saved_payload["facts"]) > 0

    # 8. Verify Verification Event Succeeded
    verif_evts = [e for e in events if e["event_type"] == "verification_completed"]
    assert len(verif_evts) == 1
    assert verif_evts[0]["status"] == "completed"
    assert verif_evts[0]["details"]["retrieved_records_count"] >= 1
    assert verif_evts[0]["details"]["isolation_passed"] is True

    # 9. Verify Final Run Completed Event Scorecard
    final_evts = [e for e in events if e["event_type"] == "run_completed"]
    assert len(final_evts) == 1
    assert final_evts[0]["status"] == "completed"
    scorecard = final_evts[0]["details"]["scorecard"]
    assert scorecard["processing_outcome"] == "SUCCESS"
    assert scorecard["pages_processed"] == 2
    assert scorecard["persisted_facts"] > 0
    assert scorecard["retrieved_facts"] >= 1
    assert scorecard["isolation_verified"] is True


@pytest.mark.asyncio
async def test_pdf_e2e_failure_and_recovery_pipeline(db_session):
    """Test failure and bounded recovery mode:

    - Step 1 context resolve injected with missing case_id.
    - Prerequisite validation blocks downstream step 2 and step 3.
    - Planning Engine replans and creates recovery context resolve step.
    - Revised plan version 2 executes recovery and unblocks downstream steps.
    - Pipeline completes with outcome RECOVERED.
    """
    runner = Ring1TestRunner(db_session=db_session)
    pdf_bytes = _create_sample_contract_pdf()
    org_id = f"org-test-{uuid.uuid4().hex[:6]}"
    case_id = f"case-pdf-{uuid.uuid4().hex[:6]}"

    events = []
    async for evt in runner.execute_pdf(
        pdf_bytes=pdf_bytes,
        filename="contract_recovery.pdf",
        organization_id=org_id,
        case_id=case_id,
        mode="failure_recovery",
    ):
        events.append(evt)

    # 1. Step 1 Failed due to fault injection
    failed_steps = [e for e in events if e["event_type"] == "step_failed"]
    assert len(failed_steps) == 1
    assert failed_steps[0]["capability"] == "context.resolve"
    assert failed_steps[0]["details"]["reason_code"] == "context_insufficient"

    # 2. Downstream Steps Blocked due to Prerequisite Validation
    blocked_steps = [e for e in events if e["event_type"] == "step_blocked"]
    assert len(blocked_steps) >= 2
    for b_step in blocked_steps:
        assert "prerequisite" in b_step["details"]["error"].lower()

    # 3. Evidence-Based Replan Triggered
    replan_req = [e for e in events if e["event_type"] == "replan_requested"]
    assert len(replan_req) == 1
    replan_done = [e for e in events if e["event_type"] == "replan_completed"]
    assert len(replan_done) == 1
    assert replan_done[0]["plan_version"] == 2
    assert len(replan_done[0]["details"]["steps_added"]) >= 1

    # 4. Revised Plan v2 Execution Succeeded
    completed_steps_v2 = [
        e for e in events if e["event_type"] == "step_completed" and e.get("plan_version") == 2
    ]
    assert len(completed_steps_v2) >= 3

    # 5. Final Scorecard shows RECOVERED
    final_evts = [e for e in events if e["event_type"] == "run_completed"]
    assert len(final_evts) == 1
    assert final_evts[0]["status"] == "completed"
    assert final_evts[0]["details"]["scorecard"]["processing_outcome"] == "RECOVERED"
    assert final_evts[0]["details"]["scorecard"]["persisted_facts"] > 0


def test_pdf_upload_api_endpoint_non_streaming(client):
    """Test POST /api/v1/ring1/upload-pdf non-streaming via FastAPI client."""
    pdf_bytes = _create_sample_contract_pdf()
    org_id = f"org-api-{uuid.uuid4().hex[:6]}"
    case_id = f"case-api-{uuid.uuid4().hex[:6]}"

    response = client.post(
        "/api/v1/ring1/upload-pdf",
        files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
        data={
            "organization_id": org_id,
            "case_id": case_id,
            "mode": "normal",
            "stream": "false",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "run_id" in data
    assert len(data["events"]) > 5
    summary = data["summary"]
    assert summary["scorecard"]["processing_outcome"] == "SUCCESS"
    assert summary["scorecard"]["pages_processed"] == 2


def test_pdf_upload_api_endpoint_streaming(client):
    """Test POST /api/v1/ring1/upload-pdf SSE streaming response."""
    pdf_bytes = _create_sample_contract_pdf()
    org_id = f"org-sse-{uuid.uuid4().hex[:6]}"
    case_id = f"case-sse-{uuid.uuid4().hex[:6]}"

    response = client.post(
        "/api/v1/ring1/upload-pdf",
        files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
        data={
            "organization_id": org_id,
            "case_id": case_id,
            "mode": "normal",
            "stream": "true",
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = response.text.split("\n\n")
    data_lines = [l for l in lines if l.startswith("data: ")]
    assert len(data_lines) > 5

    # Check that events deserialize into valid JSON objects
    parsed_events = [json.loads(l.replace("data: ", "")) for l in data_lines if l.strip()]
    event_types = [e["event_type"] for e in parsed_events]
    assert "extraction_started" in event_types
    assert "extraction_completed" in event_types
    assert "observation_persisted" in event_types
    assert "run_completed" in event_types


def test_pdf_upload_api_validation_errors(client):
    """Adversarial validation tests on PDF upload endpoint:

    - Non-PDF bytes rejected with 400.
    - Missing organization_id or case_id rejected with 400.
    """
    # 1. Non-PDF invalid signature
    resp = client.post(
        "/api/v1/ring1/upload-pdf",
        files={"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")},
        data={"organization_id": "org-1", "case_id": "case-1"},
    )
    assert resp.status_code == 400
    err_body = resp.json()
    err_msg = err_body.get("detail") or err_body.get("error", {}).get("message", "")
    assert "signature" in err_msg.lower()

    # 2. Missing case_id
    pdf_bytes = _create_sample_contract_pdf()
    resp2 = client.post(
        "/api/v1/ring1/upload-pdf",
        files={"file": ("valid.pdf", pdf_bytes, "application/pdf")},
        data={"organization_id": "org-1", "case_id": "  "},
    )
    assert resp2.status_code == 400
    err_body2 = resp2.json()
    err_msg2 = err_body2.get("detail") or err_body2.get("error", {}).get("message", "")
    assert "required" in err_msg2.lower()


def test_saved_knowledge_persistence_and_isolation(client, db_session):
    """Verify stored knowledge persists in DB and is strictly isolated between cases."""
    pdf_bytes = _create_sample_contract_pdf()
    org_id = f"org-iso-{uuid.uuid4().hex[:6]}"
    case_1 = f"case-alpha-{uuid.uuid4().hex[:6]}"
    case_2 = f"case-beta-{uuid.uuid4().hex[:6]}"

    # Upload and ingest for case_1
    resp1 = client.post(
        "/api/v1/ring1/upload-pdf",
        files={"file": ("doc_alpha.pdf", pdf_bytes, "application/pdf")},
        data={"organization_id": org_id, "case_id": case_1, "stream": "false"},
    )
    assert resp1.status_code == 200

    # Query knowledge for case_1 -> must return the records
    resp_k1 = client.get(
        "/api/v1/ring1/knowledge",
        params={"organization_id": org_id, "case_id": case_1},
    )
    assert resp_k1.status_code == 200
    data_k1 = resp_k1.json()
    assert data_k1["total"] >= 1
    assert data_k1["records"][0]["case_id"] == case_1

    # Query knowledge for case_2 -> must return 0 records (isolation guaranteed)
    resp_k2 = client.get(
        "/api/v1/ring1/knowledge",
        params={"organization_id": org_id, "case_id": case_2},
    )
    assert resp_k2.status_code == 200
    data_k2 = resp_k2.json()
    assert data_k2["total"] == 0
    assert len(data_k2["records"]) == 0

    # Verify directly via a fresh service instance (ensuring not dependent on in-memory cache)
    fresh_runner = Ring1TestRunner(db_session=db_session)
    records_fresh = fresh_runner.query_saved_knowledge(organization_id=org_id, case_id=case_1)
    assert len(records_fresh) >= 1
    assert records_fresh[0]["case_id"] == case_1
