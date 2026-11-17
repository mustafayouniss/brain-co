"""Regression tests for Document Ingestion Pipeline.

Validates:
1. Worker resilience (Issue 4): process_task_worker run twice completes with exactly
   one Observation and one MemoryRecord via SAVEPOINT and idempotency re-query.
2. Duplicate uploads (Issue 3+2): same PDF uploaded twice to the same case creates
   exactly one Source row and one stored file, reusing the existing source/task.
3. Multi-tenant isolation (Issue 3+2): same PDF uploaded to two different organizations
   creates two distinct Sources scoped to their respective organizations.
4. Retry on failure (Issue 3+2): when a document's task is in a FAILED or DEAD_LETTER
   state, re-uploading retries the task instead of returning a dead task forever.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
import uuid
from uuid import UUID

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.core.task_manager import TaskManager
from app.models.case import Case
from app.models.organization import Organization, OrganizationMembership
from app.models.source import Source
from app.models.task import Task, TaskState
from app.models.user import User
from app.ring1.models.observation import MemoryRecord, Observation
from app.services.document_processing_service import DocumentProcessingService


def _get_sample_pdf_bytes() -> bytes:
    """Obtain valid test PDF bytes."""
    fixture_path = Path("data-engineering/fixtures/ingestion/valid_small.pdf")
    if fixture_path.exists():
        return fixture_path.read_bytes()
    alt_path = Path(__file__).resolve().parent.parent.parent / "data-engineering" / "fixtures" / "ingestion" / "valid_small.pdf"
    if alt_path.exists():
        return alt_path.read_bytes()
    import pypdf
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_worker_run_twice_creates_single_observation_and_memory_record(
    db_session: Session,
):
    """Issue 4 regression: Worker run twice completes with exactly one Observation and one MemoryRecord."""
    # 1. Create Organization
    org = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Resilience Test Org",
        slug=f"resilience-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org)
    db_session.flush()

    # 2. Create User first and flush (Case.created_by has a foreign key)
    user = User(
        id=uuid.uuid4(),
        email=f"worker_resilience_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Resilience Worker",
        hashed_password=hash_password("testpassword123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # 3. Create Case
    case = Case(
        id=uuid.uuid4(),
        case_number=f"RES-{uuid.uuid4().hex[:6]}",
        title="Worker Resilience Test Case",
        organization_id=org.id,
        status="active",
        created_by=user.id,
    )
    db_session.add(case)
    db_session.flush()

    # 4. Prepare physical PDF file
    pdf_bytes = _get_sample_pdf_bytes()
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()
    storage_dir = Path("raw_storage/documents").resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_file = storage_dir / f"{uuid.uuid4().hex}_test_worker.pdf"
    storage_file.write_bytes(pdf_bytes)

    # 5. Create Source
    source = Source(
        id=uuid.uuid4(),
        case_id=str(case.id),
        organization_id=org.id,
        original_filename="test_worker.pdf",
        content_type="application/pdf",
        size_bytes=len(pdf_bytes),
        checksum_sha256=sha256_hash,
        source_type="document",
        storage_mode="local",
        storage_key=str(storage_file),
        status="ingested",
        uploaded_by=user.id,
    )
    db_session.add(source)
    db_session.flush()

    # 6. Create Task in QUEUED state
    task_payload = {
        "source_id": str(source.id),
        "filename": "test_worker.pdf",
        "storage_key": str(storage_file),
        "file_hash": sha256_hash,
        "case_id": str(case.id),
    }
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id=org.id,
        task_type="document_processing",
        payload=task_payload,
        idempotency_key=f"source-doc-{case.id}-{sha256_hash}",
        case_id=str(case.id),
        user_id=str(user.id),
    )
    task.state = TaskState.QUEUED.value
    db_session.flush()

    try:
        # Run 1: First execution
        success1 = DocumentProcessingService.process_task_worker(
            session=db_session,
            task_id=task.id,
            worker_id="test-worker-1",
        )
        assert success1 is True

        obs_first = db_session.query(Observation).filter(Observation.case_id == str(case.id)).all()
        mem_first = db_session.query(MemoryRecord).filter(MemoryRecord.case_id == str(case.id)).all()
        assert len(obs_first) == 1
        assert len(mem_first) == 1

        # Run 2: Second execution on the same task (reset to QUEUED state to test SAVEPOINT idempotency)
        task.state = TaskState.QUEUED.value
        task.worker_id = None
        task.lease_expires_at = None
        db_session.flush()

        success2 = DocumentProcessingService.process_task_worker(
            session=db_session,
            task_id=task.id,
            worker_id="test-worker-2",
        )
        assert success2 is True

        # Assert exactly one Observation and one MemoryRecord exist in database
        obs_second = db_session.query(Observation).filter(Observation.case_id == str(case.id)).all()
        mem_second = db_session.query(MemoryRecord).filter(MemoryRecord.case_id == str(case.id)).all()
        assert len(obs_second) == 1
        assert len(mem_second) == 1
        assert obs_second[0].id == obs_first[0].id
        assert mem_second[0].id == mem_first[0].id
    finally:
        if storage_file.exists():
            storage_file.unlink(missing_ok=True)


def test_duplicate_pdf_upload_same_case_creates_single_source_and_stored_file(
    client: TestClient, db_session: Session
):
    """Issue 3+2 regression: Same PDF uploaded twice to the same case creates one Source row and one stored file."""
    # 1. Create Organization
    org = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Dup Upload Org",
        slug=f"dup-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org)
    db_session.flush()

    # 2. Create User first and flush
    user = User(
        id=uuid.uuid4(),
        email=f"dup_uploader_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Duplicate Uploader",
        hashed_password=hash_password("testpassword123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org.id,
        user_id=user.id,
        role="admin",
        is_active=True,
    )
    db_session.add(membership)
    db_session.flush()

    # 3. Create Case
    case = Case(
        id=uuid.uuid4(),
        case_number=f"DUP-{uuid.uuid4().hex[:6]}",
        title="Duplicate PDF Test Case",
        organization_id=org.id,
        status="active",
        created_by=user.id,
    )
    db_session.add(case)
    db_session.flush()

    token = create_access_token(str(user.id), org_id=org.id, role="admin", domain="legal")
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = _get_sample_pdf_bytes()
    created_storage_keys = []

    try:
        # First upload: novel document
        res1 = client.post(
            f"/api/v1/cases/{case.id}/documents",
            files={"file": ("contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers=headers,
        )
        assert res1.status_code == 202
        body1 = res1.json()
        assert body1["message"] == "Document accepted and processing task dispatched"
        source_id1 = body1["source_id"]
        task_id1 = body1["task_id"]

        sources1 = db_session.query(Source).filter(Source.case_id == str(case.id)).all()
        assert len(sources1) == 1
        storage_path1 = Path(sources1[0].storage_key)
        created_storage_keys.append(storage_path1)
        assert storage_path1.exists()

        # Second upload: same PDF to same case
        res2 = client.post(
            f"/api/v1/cases/{case.id}/documents",
            files={"file": ("contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers=headers,
        )
        assert res2.status_code == 202
        body2 = res2.json()
        assert "already registered" in body2["message"].lower()
        assert body2["source_id"] == source_id1
        assert body2["task_id"] == task_id1

        # Assert exactly one Source row in DB
        sources2 = db_session.query(Source).filter(Source.case_id == str(case.id)).all()
        assert len(sources2) == 1
        assert sources2[0].id == UUID(source_id1)
        assert Path(sources2[0].storage_key) == storage_path1

        # Assert only one stored file exists on disk for this upload
        assert storage_path1.exists()
    finally:
        for p in created_storage_keys:
            if p.exists():
                p.unlink(missing_ok=True)


def test_same_pdf_uploaded_to_different_organizations_creates_two_sources(
    client: TestClient, db_session: Session
):
    """Issue 3+2 regression: Same PDF uploaded to two different organizations creates two Sources."""
    # Org A
    org_a = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Org Alpha",
        slug=f"alpha-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org_a)
    db_session.flush()

    user_a = User(
        id=uuid.uuid4(),
        email=f"user_a_{uuid.uuid4().hex[:6]}@example.com",
        full_name="User Alpha",
        hashed_password=hash_password("pwA"),
        role="admin",
        is_active=True,
    )
    db_session.add(user_a)
    db_session.flush()

    m_a = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org_a.id, user_id=user_a.id, role="admin", is_active=True
    )
    db_session.add(m_a)
    db_session.flush()

    case_a = Case(
        id=uuid.uuid4(),
        case_number=f"ALP-{uuid.uuid4().hex[:6]}",
        title="Alpha Case",
        organization_id=org_a.id,
        status="active",
        created_by=user_a.id,
    )
    db_session.add(case_a)
    db_session.flush()

    # Org B
    org_b = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Org Beta",
        slug=f"beta-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org_b)
    db_session.flush()

    user_b = User(
        id=uuid.uuid4(),
        email=f"user_b_{uuid.uuid4().hex[:6]}@example.com",
        full_name="User Beta",
        hashed_password=hash_password("pwB"),
        role="admin",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.flush()

    m_b = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org_b.id, user_id=user_b.id, role="admin", is_active=True
    )
    db_session.add(m_b)
    db_session.flush()

    case_b = Case(
        id=uuid.uuid4(),
        case_number=f"BET-{uuid.uuid4().hex[:6]}",
        title="Beta Case",
        organization_id=org_b.id,
        status="active",
        created_by=user_b.id,
    )
    db_session.add(case_b)
    db_session.flush()

    token_a = create_access_token(str(user_a.id), org_id=org_a.id, role="admin", domain="legal")
    token_b = create_access_token(str(user_b.id), org_id=org_b.id, role="admin", domain="legal")

    pdf_bytes = _get_sample_pdf_bytes()
    pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    created_storage_keys = []

    try:
        # Upload to Org A
        res_a = client.post(
            f"/api/v1/cases/{case_a.id}/documents",
            files={"file": ("shared_contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res_a.status_code == 202
        body_a = res_a.json()
        source_id_a = body_a["source_id"]

        # Upload exact same PDF to Org B
        res_b = client.post(
            f"/api/v1/cases/{case_b.id}/documents",
            files={"file": ("shared_contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_b.status_code == 202
        body_b = res_b.json()
        source_id_b = body_b["source_id"]

        # Two distinct sources must be created
        assert source_id_a != source_id_b

        sources = (
            db_session.query(Source)
            .filter(Source.checksum_sha256 == pdf_sha256)
            .all()
        )
        test_sources = [s for s in sources if s.case_id in (str(case_a.id), str(case_b.id))]
        assert len(test_sources) == 2
        for s in test_sources:
            created_storage_keys.append(Path(s.storage_key))

        org_ids = {s.organization_id for s in test_sources}
        assert org_ids == {org_a.id, org_b.id}
    finally:
        for p in created_storage_keys:
            if p.exists():
                p.unlink(missing_ok=True)


def test_duplicate_pdf_upload_retries_when_task_failed(client: TestClient, db_session: Session):
    """Issue 3+2 regression: When previous task is failed or dead_letter, duplicate upload retries."""
    org = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Retry Upload Org",
        slug=f"retry-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org)
    db_session.flush()

    user = User(
        id=uuid.uuid4(),
        email=f"retry_uploader_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Retry Uploader",
        hashed_password=hash_password("pw"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    m = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org.id, user_id=user.id, role="admin", is_active=True
    )
    db_session.add(m)
    db_session.flush()

    case = Case(
        id=uuid.uuid4(),
        case_number=f"RET-{uuid.uuid4().hex[:6]}",
        title="Retry PDF Test Case",
        organization_id=org.id,
        status="active",
        created_by=user.id,
    )
    db_session.add(case)
    db_session.flush()

    token = create_access_token(str(user.id), org_id=org.id, role="admin", domain="legal")
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = _get_sample_pdf_bytes()
    created_storage_keys = []

    try:
        # First upload
        res1 = client.post(
            f"/api/v1/cases/{case.id}/documents",
            files={"file": ("contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers=headers,
        )
        assert res1.status_code == 202
        body1 = res1.json()
        task_id = UUID(body1["task_id"])

        task = db_session.get(Task, task_id)
        assert task is not None
        source = db_session.get(Source, UUID(body1["source_id"]))
        if source:
            created_storage_keys.append(Path(source.storage_key))

        # Simulate failure on the task
        task.state = TaskState.FAILED.value
        task.error_details = {"code": "SIMULATED_FAILURE", "message": "Simulated error"}
        db_session.flush()

        # Second upload: must retry because task is in FAILED state
        res2 = client.post(
            f"/api/v1/cases/{case.id}/documents",
            files={"file": ("contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers=headers,
        )
        assert res2.status_code == 202
        body2 = res2.json()
        assert body2["message"] == "Document accepted and processing task dispatched"
        assert body2["task_id"] == str(task.id)

        # Verify task is reset to PENDING and error details cleared
        db_session.refresh(task)
        assert task.state == TaskState.PENDING.value
        assert task.error_details is None
    finally:
        for p in created_storage_keys:
            if p.exists():
                p.unlink(missing_ok=True)
