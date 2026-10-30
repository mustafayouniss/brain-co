"""Tests for Transactional Outbox Dispatcher, Generation Fencing, and Recovery."""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy.orm import Session

from app.core.outbox_dispatcher import OutboxDispatcher
from app.core.task_manager import TaskManager
from app.models.task import OutboxStatus, Task, TaskOutbox, TaskState


def test_claim_pending_transitions_task_to_queued(db_session: Session):
    """Claiming outbox record atomically transitions task to QUEUED and outbox to DISPATCHING."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={"memo_id": "m-123"},
    )
    assert task.state == TaskState.PENDING.value

    # Claim pending records
    claimed = OutboxDispatcher.claim_pending_records(session=db_session, limit=10, lease_seconds=30)
    assert len(claimed) >= 1
    outbox_id, task_id, queue_name, payload, dispatch_gen = claimed[0]
    assert task_id == task.id
    assert dispatch_gen == 1

    # Verify task state transitioned to QUEUED before Redis enqueue
    db_session.refresh(task)
    assert task.state == TaskState.QUEUED.value

    # Verify outbox status is DISPATCHING
    outbox = db_session.get(TaskOutbox, outbox_id)
    assert outbox.status == OutboxStatus.DISPATCHING.value
    assert outbox.dispatch_generation == 1
    assert outbox.dispatch_lease_expires_at > datetime.now(timezone.utc)


def test_dispatcher_recovery_after_lease_expiry(db_session: Session):
    """Abandoned dispatch leases are reclaimed on next poll with incremented generation."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={},
    )
    outbox = db_session.query(TaskOutbox).filter(TaskOutbox.task_id == task.id).first()
    outbox.status = OutboxStatus.DISPATCHING.value
    outbox.dispatch_generation = 1
    outbox.dispatch_lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.flush()

    # Next dispatcher poll reclaims the abandoned record
    claimed = OutboxDispatcher.claim_pending_records(session=db_session, limit=10, lease_seconds=30)
    reclaimed_ids = [c[0] for c in claimed]
    assert outbox.id in reclaimed_ids

    db_session.refresh(outbox)
    assert outbox.dispatch_generation == 2
    assert outbox.dispatch_lease_expires_at > datetime.now(timezone.utc)


def test_stale_ack_rejected(db_session: Session):
    """Acknowledgment with older generation is rejected, preventing race overwrites."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={},
    )
    outbox = db_session.query(TaskOutbox).filter(TaskOutbox.task_id == task.id).first()
    outbox.status = OutboxStatus.DISPATCHING.value
    outbox.dispatch_generation = 2
    db_session.flush()

    # Stale ACK with generation 1 (from previous timed-out dispatch attempt)
    stale_ack = OutboxDispatcher.acknowledge_dispatch(
        session=db_session,
        outbox_id=outbox.id,
        claimed_dispatch_generation=1,
    )
    assert stale_ack is False
    db_session.refresh(outbox)
    assert outbox.status == OutboxStatus.DISPATCHING.value  # Not marked DISPATCHED

    # Valid ACK with generation 2
    valid_ack = OutboxDispatcher.acknowledge_dispatch(
        session=db_session,
        outbox_id=outbox.id,
        claimed_dispatch_generation=2,
    )
    assert valid_ack is True
    db_session.refresh(outbox)
    assert outbox.status == OutboxStatus.DISPATCHED.value
    assert outbox.dispatched_at is not None


def test_admin_retry_invalidates_stale_dispatcher(db_session: Session):
    """Admin retry resets outbox to PENDING and bumps generation, invalidating stale dispatchers."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={},
    )
    outbox = db_session.query(TaskOutbox).filter(TaskOutbox.task_id == task.id).first()
    outbox.status = OutboxStatus.FAILED_DISPATCH.value
    outbox.dispatch_generation = 3
    db_session.flush()

    # Admin retry
    reset = OutboxDispatcher.admin_retry_outbox(session=db_session, outbox_id=outbox.id)
    assert reset is True

    db_session.refresh(outbox)
    assert outbox.status == OutboxStatus.PENDING.value
    assert outbox.dispatch_generation == 4  # Monotonically incremented
    assert outbox.dispatch_attempts == 0

    # Stale dispatcher attempting to record failure at generation 3 is rejected
    stale_record = OutboxDispatcher.record_terminal_dispatch_failure(
        session=db_session,
        outbox_id=outbox.id,
        task_id=task.id,
        claimed_dispatch_generation=3,
        max_attempts=5,
    )
    assert stale_record is False


def test_terminal_dispatch_failure_does_not_corrupt_running_task(db_session: Session):
    """Exhausted dispatch attempts do not mark RUNNING or SUCCEEDED tasks as FAILED."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_memo_analysis",
        payload={},
    )
    # Simulate worker already claiming task and moving to RUNNING
    task.state = TaskState.RUNNING.value
    task.worker_id = "worker-1"
    task.lease_generation = 1

    outbox = db_session.query(TaskOutbox).filter(TaskOutbox.task_id == task.id).first()
    outbox.status = OutboxStatus.DISPATCHING.value
    outbox.dispatch_generation = 1
    outbox.dispatch_attempts = 5
    db_session.flush()

    # Record terminal dispatch failure
    failed = OutboxDispatcher.record_terminal_dispatch_failure(
        session=db_session,
        outbox_id=outbox.id,
        task_id=task.id,
        claimed_dispatch_generation=1,
        max_attempts=5,
    )
    assert failed is True

    # Outbox is marked FAILED_DISPATCH
    db_session.refresh(outbox)
    assert outbox.status == OutboxStatus.FAILED_DISPATCH.value

    # BUT the task itself remains RUNNING (not corrupted)
    db_session.refresh(task)
    assert task.state == TaskState.RUNNING.value
    assert task.worker_id == "worker-1"
