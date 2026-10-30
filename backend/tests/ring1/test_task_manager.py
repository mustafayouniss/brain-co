"""Tests for PostgreSQL-backed Durable Task Lifecycle, Worker Claiming, and Lease Fencing."""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy.orm import Session

from app.core.task_manager import StaleWorkerLeaseError, TaskManager
from app.models.audit import AuditEvent
from app.models.task import OutboxStatus, Task, TaskOutbox, TaskState


def test_create_task_with_outbox_atomic(db_session: Session):
    """Task creation and outbox event creation must be atomic in PostgreSQL."""
    idempotency_key = f"idem-{uuid.uuid4().hex}"
    task, is_new = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={"contract_id": "c-999"},
        idempotency_key=idempotency_key,
    )
    assert is_new is True
    assert task is not None
    assert task.state == TaskState.PENDING.value
    assert task.organization_id == "org-cairo"
    assert task.case_id == "case-101"
    assert task.lease_generation == 0

    # Verify matching outbox record created in the same atomic transaction
    outbox = db_session.query(TaskOutbox).filter(TaskOutbox.task_id == task.id).first()
    assert outbox is not None
    assert outbox.status == OutboxStatus.PENDING.value
    assert outbox.dispatch_generation == 0

    # Idempotent second creation: returns existing task without error
    duplicate_task, is_novel = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={"contract_id": "c-999"},
        idempotency_key=idempotency_key,
    )
    assert is_novel is False
    assert duplicate_task.id == task.id


def test_worker_claim_and_concurrent_conflict(db_session: Session):
    """Worker claims QUEUED task atomically; second worker cannot claim the same task."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={"contract_id": "c-999"},
    )
    # Simulate Outbox dispatch transitioning state to QUEUED
    task.state = TaskState.QUEUED.value
    db_session.flush()

    # Worker A claims task
    gen_a = TaskManager.claim_task_for_worker(
        session=db_session,
        task_id=task.id,
        worker_id="worker-node-A",
        lease_duration_seconds=30,
    )
    assert gen_a == 1
    db_session.refresh(task)
    assert task.worker_id == "worker-node-A"
    assert task.state == TaskState.RUNNING.value
    assert task.lease_generation == 1
    assert task.lease_expires_at > datetime.now(timezone.utc)

    # Worker B tries to claim the same task concurrently — must return None
    gen_b = TaskManager.claim_task_for_worker(
        session=db_session,
        task_id=task.id,
        worker_id="worker-node-B",
        lease_duration_seconds=30,
    )
    assert gen_b is None


def test_stale_worker_generation_fencing(db_session: Session):
    """Worker with older generation is rejected when committing writes."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={"contract_id": "c-999"},
    )
    task.state = TaskState.QUEUED.value
    db_session.flush()

    # Claim at generation 1
    gen = TaskManager.claim_task_for_worker(db_session, task.id, "worker-node-A")
    assert gen == 1

    # Simulate reaper or admin incrementing generation to 2
    task.lease_generation = 2
    db_session.flush()

    # Worker A (holding generation 1) attempts commit — must raise StaleWorkerLeaseError
    with pytest.raises(StaleWorkerLeaseError) as exc_info:
        TaskManager.commit_task_success(
            session=db_session,
            task_id=task.id,
            current_generation=1,
            result={"analysis": "done"},
        )
    assert "revoked on completion" in str(exc_info.value)


def test_heartbeat_renewal_and_stale_rejection(db_session: Session):
    """Heartbeat extends lease if generation matches; rejected if superseded."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={},
    )
    task.state = TaskState.QUEUED.value
    db_session.flush()

    gen = TaskManager.claim_task_for_worker(db_session, task.id, "worker-node-A", lease_duration_seconds=10)
    db_session.refresh(task)
    initial_expiry = task.lease_expires_at

    # Valid heartbeat
    renewed = TaskManager.renew_heartbeat(
        session=db_session,
        task_id=task.id,
        worker_id="worker-node-A",
        current_generation=gen,
        extension_seconds=60,
    )
    assert renewed is True
    db_session.refresh(task)
    assert task.lease_expires_at > initial_expiry

    # Stale generation heartbeat
    stale_renewed = TaskManager.renew_heartbeat(
        session=db_session,
        task_id=task.id,
        worker_id="worker-node-A",
        current_generation=0,
        extension_seconds=60,
    )
    assert stale_renewed is False


def test_reaper_reclaims_expired_leases(db_session: Session):
    """Reaper reclaims RUNNING tasks with expired leases and increments generation."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={},
    )
    task.state = TaskState.RUNNING.value
    task.worker_id = "dead-worker"
    task.lease_generation = 1
    task.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.flush()

    reclaimed_ids = TaskManager.reclaim_stale_tasks(session=db_session)
    assert task.id in reclaimed_ids

    db_session.refresh(task)
    assert task.state == TaskState.RETRYING.value
    assert task.worker_id is None
    assert task.lease_generation == 2
    assert task.retry_count == 1


def test_transient_failure_and_retry(db_session: Session):
    """Transient failure increments retry count and schedules outbox retry."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={},
    )
    task.state = TaskState.RUNNING.value
    task.worker_id = "worker-node-A"
    task.lease_generation = 1
    task.retry_count = 0
    task.max_retries = 3
    db_session.flush()

    res = TaskManager.commit_task_transient_failure(
        session=db_session,
        task_id=task.id,
        current_generation=1,
        error_data={"error": "LLM rate limit"},
        backoff_seconds=15,
    )
    assert res is True
    db_session.refresh(task)
    assert task.state == TaskState.RETRYING.value
    assert task.retry_count == 1

    # Verify outbox retry row
    retry_outbox = db_session.query(TaskOutbox).filter(
        TaskOutbox.task_id == task.id,
        TaskOutbox.status == OutboxStatus.PENDING.value,
        TaskOutbox.scheduled_for.is_not(None),
    ).first()
    assert retry_outbox is not None


def test_retry_exhaustion_transitions_to_dead_letter(db_session: Session):
    """Exhausting retry limit transitions task to DEAD_LETTER."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={},
    )
    task.state = TaskState.RUNNING.value
    task.worker_id = "worker-node-A"
    task.lease_generation = 1
    task.retry_count = 3
    task.max_retries = 3
    db_session.flush()

    res = TaskManager.commit_task_retry_exhaustion(
        session=db_session,
        task_id=task.id,
        current_generation=1,
        error_data={"error": "Max retries exceeded"},
    )
    assert res is True
    db_session.refresh(task)
    assert task.state == TaskState.DEAD_LETTER.value


def test_permanent_failure_transitions_to_failed(db_session: Session):
    """Permanent error transitions immediately to FAILED without retry."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={},
    )
    task.state = TaskState.RUNNING.value
    task.worker_id = "worker-node-A"
    task.lease_generation = 1
    task.retry_count = 0
    db_session.flush()

    res = TaskManager.commit_task_permanent_failure(
        session=db_session,
        task_id=task.id,
        current_generation=1,
        error_data={"error": "Invalid schema syntax"},
    )
    assert res is True
    db_session.refresh(task)
    assert task.state == TaskState.FAILED.value
    assert task.retry_count == 0


def test_task_success_commits_audit_atomically(db_session: Session):
    """Task success commits result and audit event atomically in PostgreSQL."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={"memo_id": "m-123"},
    )
    task.state = TaskState.RUNNING.value
    task.worker_id = "worker-node-A"
    task.lease_generation = 1
    db_session.flush()

    res = TaskManager.commit_task_success(
        session=db_session,
        task_id=task.id,
        current_generation=1,
        result={"summary": "Risk analysis complete", "risk_score": 0.15},
    )
    assert res is True
    db_session.refresh(task)
    assert task.state == TaskState.SUCCEEDED.value
    assert task.result["risk_score"] == 0.15


def test_replay_task(db_session: Session):
    """Replay task creates a new linked task in PENDING state and an outbox entry."""
    original_task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={"contract_id": "c-123"},
    )
    original_task.state = TaskState.FAILED.value
    db_session.flush()

    new_task, outbox = TaskManager.replay_task(session=db_session, original_task_id=original_task.id)
    assert new_task.id != original_task.id
    assert new_task.state == TaskState.PENDING.value
    assert new_task.replayed_from_task_id == original_task.id
    assert outbox.task_id == new_task.id
    assert outbox.status == OutboxStatus.PENDING.value

    db_session.refresh(original_task)
    assert original_task.replayed_to_task_id == new_task.id


def test_database_contract_consistency():
    """Verify consistent state naming across Task, TaskOutbox, and AuditEvent models."""
    from sqlalchemy import inspect
    from app.models.audit import AuditEvent

    task_cols = [c.name for c in inspect(Task).columns]
    assert "state" in task_cols, "Task model must define 'state' column"
    assert "status" not in task_cols, "Task model must not define conflicting 'status' column"

    outbox_cols = [c.name for c in inspect(TaskOutbox).columns]
    assert "status" in outbox_cols, "TaskOutbox model must define 'status' column"

    audit_cols = [c.name for c in inspect(AuditEvent).columns]
    assert "previous_state" in audit_cols, "AuditEvent must record 'previous_state'"
    assert "new_state" in audit_cols, "AuditEvent must record 'new_state'"

    # Verify exact valid TaskState transitions
    valid_states = {s.value for s in TaskState}
    assert valid_states == {"PENDING", "QUEUED", "RUNNING", "RETRYING", "SUCCEEDED", "FAILED", "DEAD_LETTER"}


def test_stale_worker_cannot_commit_side_effects(db_session: Session):
    """A worker whose generation was superseded cannot assert fence or commit side effects."""
    from app.ring1.models.observation import MemoryRecord, Observation

    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={"contract_id": "c-123"},
    )
    task.state = TaskState.QUEUED.value
    db_session.flush()

    # Worker 1 claims task at generation 1
    gen1 = TaskManager.claim_task_for_worker(session=db_session, task_id=task.id, worker_id="worker-1")
    assert gen1 == 1

    # Lease expires and reaper reclaims task, bumping generation to 2
    task.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.flush()
    reclaimed = TaskManager.reclaim_stale_tasks(session=db_session)
    assert task.id in reclaimed

    # Worker 2 claims task at generation 3 (reclaimed was RETRYING gen 2, worker 2 claims gen 3)
    gen2 = TaskManager.claim_task_for_worker(session=db_session, task_id=task.id, worker_id="worker-2")
    assert gen2 == 3

    # Worker 1 wakes up and attempts to write an observation or assert fence under superseded gen 1
    with pytest.raises(StaleWorkerLeaseError):
        TaskManager.assert_worker_fence(session=db_session, task_id=task.id, current_generation=gen1)

    # Worker 1 attempting commit_task_success is strictly rejected
    with pytest.raises(StaleWorkerLeaseError):
        TaskManager.commit_task_success(
            session=db_session,
            task_id=task.id,
            current_generation=gen1,
            result={"stale": "data"},
        )

    # Ensure no side-effects or state overwrite from worker 1
    db_session.refresh(task)
    assert task.lease_generation == 3
    assert task.worker_id == "worker-2"
    assert task.state == TaskState.RUNNING.value

