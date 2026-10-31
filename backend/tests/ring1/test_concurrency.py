"""Concurrency and failure-window tests for TaskManager and OutboxDispatcher.

Exercises:
1. Concurrent worker claim mutual exclusion (atomic claim).
2. Stale worker race against reaper and replacement worker.
3. Outbox Redis ACK loss failure window (message enqueued, dispatcher crashes before ACK,
   worker completes task, outbox retries without corrupting SUCCEEDED state).
4. Duplicate queue delivery suppression.
"""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy.orm import Session

from app.core.outbox_dispatcher import OutboxDispatcher
from app.core.task_manager import StaleWorkerLeaseError, TaskManager
from app.models.task import OutboxStatus, Task, TaskOutbox, TaskState


def test_concurrent_worker_claim_mutual_exclusion(db_session: Session):
    """Two concurrent workers attempting to claim the same queued task: exactly one succeeds."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_analysis",
        payload={"contract_id": "c-999"},
    )
    task.state = TaskState.QUEUED.value
    db_session.flush()

    # Worker A claims
    claim_a = TaskManager.claim_task_for_worker(
        session=db_session,
        task_id=task.id,
        worker_id="worker-A",
        lease_duration_seconds=300,
    )
    assert claim_a == 1

    # Worker B attempts concurrent claim on the same task
    claim_b = TaskManager.claim_task_for_worker(
        session=db_session,
        task_id=task.id,
        worker_id="worker-B",
        lease_duration_seconds=300,
    )
    # Claim must be rejected because task is already RUNNING
    assert claim_b is None

    db_session.refresh(task)
    assert task.worker_id == "worker-A"
    assert task.lease_generation == 1
    assert task.state == TaskState.RUNNING.value


def test_stale_worker_race_with_reaper(db_session: Session):
    """Worker 1 lease expires, reaper reclaims, Worker 2 claims. Worker 1 writes are rejected."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_analysis",
        payload={"contract_id": "c-999"},
    )
    task.state = TaskState.QUEUED.value
    db_session.flush()

    # 1. Worker 1 claims task
    gen1 = TaskManager.claim_task_for_worker(
        session=db_session,
        task_id=task.id,
        worker_id="worker-1",
        lease_duration_seconds=10,
    )
    assert gen1 == 1

    # 2. Worker 1 experiences network freeze/delay. Lease expires.
    task.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=5)
    db_session.flush()

    # 3. Reaper runs and reclaims the stale task
    reclaimed = TaskManager.reclaim_stale_tasks(session=db_session)
    assert task.id in reclaimed
    db_session.refresh(task)
    assert task.state == TaskState.RETRYING.value
    assert task.lease_generation == 2

    # 4. Worker 2 claims the retrying task
    gen2 = TaskManager.claim_task_for_worker(
        session=db_session,
        task_id=task.id,
        worker_id="worker-2",
        lease_duration_seconds=300,
    )
    assert gen2 == 3
    db_session.refresh(task)
    assert task.state == TaskState.RUNNING.value
    assert task.worker_id == "worker-2"

    # 5. Worker 1 wakes up and attempts to commit results using expired generation 1
    with pytest.raises(StaleWorkerLeaseError):
        TaskManager.commit_task_success(
            session=db_session,
            task_id=task.id,
            current_generation=gen1,
            result={"analysis": "stale_result_from_worker_1"},
        )

    # 6. Worker 2 commits results using valid generation 3 -> succeeds
    success = TaskManager.commit_task_success(
        session=db_session,
        task_id=task.id,
        current_generation=gen2,
        result={"analysis": "valid_result_from_worker_2"},
    )
    assert success is True
    db_session.refresh(task)
    assert task.state == TaskState.SUCCEEDED.value
    assert task.result["analysis"] == "valid_result_from_worker_2"


def test_outbox_redis_ack_loss_window_recovery(db_session: Session):
    """Failure Window: Redis accepts message, dispatcher crashes before ACK, worker completes task.
    Outbox retries/exhaustion must NOT corrupt the SUCCEEDED task.
    """
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_analysis",
        payload={"contract_id": "c-999"},
    )

    # 1. Dispatcher claims pending outbox
    claimed = OutboxDispatcher.claim_pending_records(session=db_session, limit=10, lease_seconds=10)
    assert len(claimed) >= 1
    outbox_id, task_id, queue_name, payload, dispatch_gen1 = claimed[0]

    db_session.refresh(task)
    assert task.state == TaskState.QUEUED.value

    # 2. Redis receives message, but Dispatcher crashes BEFORE calling acknowledge_dispatch!
    # Worker receives the message from Redis immediately
    worker_gen = TaskManager.claim_task_for_worker(
        session=db_session,
        task_id=task.id,
        worker_id="fast-worker",
    )
    assert worker_gen == 1

    # Worker executes task and commits SUCCEEDED
    completed = TaskManager.commit_task_success(
        session=db_session,
        task_id=task.id,
        current_generation=worker_gen,
        result={"verdict": "valid_contract"},
    )
    assert completed is True
    db_session.refresh(task)
    assert task.state == TaskState.SUCCEEDED.value

    # 3. Meanwhile, the unacknowledged outbox record's lease expires
    outbox = db_session.get(TaskOutbox, outbox_id)
    outbox.dispatch_lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=5)
    outbox.dispatch_attempts = 5  # Simulate hitting max retry attempts
    db_session.flush()

    # 4. Outbox recovery runner detects exhausted attempts and records terminal failure
    failed_outbox = OutboxDispatcher.record_terminal_dispatch_failure(
        session=db_session,
        outbox_id=outbox.id,
        task_id=task.id,
        claimed_dispatch_generation=outbox.dispatch_generation,
        max_attempts=5,
    )
    assert failed_outbox is True

    # 5. Crucial verification: Outbox is marked FAILED_DISPATCH, but Task remains SUCCEEDED!
    db_session.refresh(outbox)
    assert outbox.status == OutboxStatus.FAILED_DISPATCH.value

    db_session.refresh(task)
    assert task.state == TaskState.SUCCEEDED.value
    assert task.result == {"verdict": "valid_contract"}


def test_duplicate_queue_delivery_suppression(db_session: Session):
    """Broker duplicate delivery: second worker delivery is rejected when task is already SUCCEEDED."""
    task, _ = TaskManager.create_task_with_outbox(
        session=db_session,
        organization_id="org-cairo",
        case_id="case-101",
        task_type="legal_analysis",
        payload={"contract_id": "c-999"},
    )
    task.state = TaskState.QUEUED.value
    db_session.flush()

    # Worker 1 claims and completes task
    gen1 = TaskManager.claim_task_for_worker(session=db_session, task_id=task.id, worker_id="worker-1")
    TaskManager.commit_task_success(
        session=db_session,
        task_id=task.id,
        current_generation=gen1,
        result={"status": "finished"},
    )
    db_session.refresh(task)
    assert task.state == TaskState.SUCCEEDED.value

    # Duplicate message arrives at Worker 2
    claim2 = TaskManager.claim_task_for_worker(session=db_session, task_id=task.id, worker_id="worker-2")
    assert claim2 is None, "Duplicate delivery must be rejected when task is already SUCCEEDED"

    db_session.refresh(task)
    assert task.state == TaskState.SUCCEEDED.value
    assert task.worker_id == "worker-1"
