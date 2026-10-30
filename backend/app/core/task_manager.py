"""Durable Task Lifecycle & Worker Fencing Manager for Ring 1.

PostgreSQL is the single authoritative source of truth for task states.
Adopts at-least-once execution semantics with monotonic lease generation fencing.
Does not assume exactly-once distributed execution.
Requires all task side effects and engine result writes to be idempotent.
Atomic worker claiming prevents concurrent ownership, and generation fencing
rejects stale worker commits after lease expiry or revocation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from typing import Any, Optional
import uuid
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.audit import AuditService
from app.models.task import OutboxStatus, Task, TaskOutbox, TaskState


class StaleWorkerLeaseError(Exception):
    """Raised when a worker attempts to commit results after its lease has been superseded."""


class TaskManager:
    """Authoritative task ledger operations in PostgreSQL."""

    @staticmethod
    def create_task_with_outbox(
        session: Session,
        organization_id: str,
        task_type: str,
        payload: dict[str, Any],
        *,
        idempotency_key: Optional[str] = None,
        case_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        queue_name: str = "ring1_tasks",
    ) -> tuple[Task, bool]:
        """Atomically create a Task and its corresponding Outbox entry in a single transaction.
        
        Uses ON CONFLICT DO NOTHING to handle concurrent/duplicate submissions safely
        without aborting the active transaction block.
        Returns: (Task instance, is_new: bool).
        """
        task_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # 1. Attempt novel insert using ON CONFLICT DO NOTHING (handling partial unique index)
        if idempotency_key:
            insert_stmt = (
                pg_insert(Task)
                .values(
                    id=task_id,
                    organization_id=organization_id,
                    case_id=case_id,
                    user_id=user_id,
                    task_type=task_type,
                    state=TaskState.PENDING.value,
                    idempotency_key=idempotency_key,
                    payload=payload,
                    correlation_id=correlation_id,
                    created_at=now,
                    updated_at=now,
                )
                .on_conflict_do_nothing(
                    index_elements=["organization_id", "idempotency_key"],
                    index_where=sa.text("idempotency_key IS NOT NULL"),
                )
                .returning(Task.id)
            )
        else:
            insert_stmt = (
                sa.insert(Task)
                .values(
                    id=task_id,
                    organization_id=organization_id,
                    case_id=case_id,
                    user_id=user_id,
                    task_type=task_type,
                    state=TaskState.PENDING.value,
                    idempotency_key=None,
                    payload=payload,
                    correlation_id=correlation_id,
                    created_at=now,
                    updated_at=now,
                )
                .returning(Task.id)
            )

        result = session.execute(insert_stmt).scalar_one_or_none()

        if result is not None:
            # Insert was novel: create Outbox row in the same transaction
            outbox_row = TaskOutbox(
                id=uuid.uuid4(),
                task_id=task_id,
                queue_name=queue_name,
                payload={"task_id": str(task_id), "organization_id": organization_id, "case_id": case_id},
                status=OutboxStatus.PENDING.value,
                dispatch_generation=0,
                dispatch_attempts=0,
                created_at=now,
                updated_at=now,
            )
            session.add(outbox_row)
            session.flush()

            AuditService.record_event(
                session,
                organization_id=organization_id,
                engine_name="task_manager",
                action="task_created",
                task_id=task_id,
                case_id=case_id,
                actor_ref=user_id,
                new_state=TaskState.PENDING.value,
                correlation_id=correlation_id,
            )

            task = session.get(Task, task_id)
            return task, True

        # Conflict occurred cleanly: query existing task within the active healthy transaction
        existing_task = (
            session.query(Task)
            .filter(
                Task.organization_id == organization_id,
                Task.idempotency_key == idempotency_key,
            )
            .first()
        )
        return existing_task, False

    @staticmethod
    def claim_task_for_worker(
        session: Session,
        task_id: UUID,
        worker_id: str,
        lease_duration_seconds: int = 300,
    ) -> Optional[int]:
        """Atomically claim a queued/retrying task for execution.
        
        Assigns worker ownership and increments lease_generation monotonically.
        Returns the new lease_generation token, or None if already claimed/running (duplicate delivery).
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=lease_duration_seconds)

        stmt = (
            sa.update(Task)
            .where(
                Task.id == task_id,
                Task.state.in_([TaskState.QUEUED.value, TaskState.RETRYING.value]),
            )
            .values(
                state=TaskState.RUNNING.value,
                worker_id=worker_id,
                lease_generation=Task.lease_generation + 1,
                lease_expires_at=expires_at,
                updated_at=now,
            )
            .returning(Task.lease_generation)
        )

        new_generation = session.execute(stmt).scalar_one_or_none()
        if new_generation is not None:
            session.flush()
        return new_generation

    @staticmethod
    def renew_heartbeat(
        session: Session,
        task_id: UUID,
        worker_id: str,
        current_generation: int,
        extension_seconds: int = 300,
    ) -> bool:
        """Renew worker lease strictly requiring active RUNNING state and matching generation."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=extension_seconds)

        stmt = (
            sa.update(Task)
            .where(
                Task.id == task_id,
                Task.state == TaskState.RUNNING.value,
                Task.worker_id == worker_id,
                Task.lease_generation == current_generation,
                Task.lease_expires_at > now,
            )
            .values(lease_expires_at=expires_at, updated_at=now)
            .returning(Task.id)
        )
        renewed = session.execute(stmt).scalar_one_or_none()
        return renewed is not None

    @staticmethod
    def assert_worker_fence(
        session: Session,
        task_id: UUID,
        current_generation: int,
    ) -> Task:
        """Assert active lease ownership under exclusive row lock within the worker's transaction."""
        task = (
            session.query(Task)
            .filter(
                Task.id == task_id,
                Task.lease_generation == current_generation,
                Task.state == TaskState.RUNNING.value,
            )
            .with_for_update()
            .first()
        )
        if not task:
            raise StaleWorkerLeaseError(
                f"Worker lease generation {current_generation} revoked or expired for task {task_id}"
            )
        return task

    @classmethod
    def commit_task_success(
        cls,
        session: Session,
        task_id: UUID,
        current_generation: int,
        result: dict[str, Any],
    ) -> bool:
        """Atomically transition task to SUCCEEDED enforcing lease generation fence."""
        now = datetime.now(timezone.utc)
        stmt = (
            sa.update(Task)
            .where(
                Task.id == task_id,
                Task.lease_generation == current_generation,
                Task.state == TaskState.RUNNING.value,
            )
            .values(
                state=TaskState.SUCCEEDED.value,
                result=result,
                lease_expires_at=None,
                updated_at=now,
            )
            .returning(Task.id)
        )
        updated = session.execute(stmt).scalar_one_or_none()
        if not updated:
            raise StaleWorkerLeaseError(f"Lease generation {current_generation} revoked on completion for task {task_id}")
        return True

    @classmethod
    def commit_task_transient_failure(
        cls,
        session: Session,
        task_id: UUID,
        current_generation: int,
        error_data: dict[str, Any],
        backoff_seconds: int,
        queue_name: str = "ring1_tasks",
    ) -> bool:
        """Atomically record transient failure, increment retry count, and schedule Outbox retry."""
        now = datetime.now(timezone.utc)
        scheduled_for = now + timedelta(seconds=backoff_seconds)

        stmt = (
            sa.update(Task)
            .where(
                Task.id == task_id,
                Task.lease_generation == current_generation,
                Task.state == TaskState.RUNNING.value,
                Task.retry_count < Task.max_retries,
            )
            .values(
                state=TaskState.RETRYING.value,
                retry_count=Task.retry_count + 1,
                lease_expires_at=None,
                error_details=error_data,
                updated_at=now,
            )
            .returning(Task.organization_id, Task.case_id)
        )
        row = session.execute(stmt).first()
        if not row:
            # If retry limit reached or lease superseded:
            return cls.commit_task_retry_exhaustion(session, task_id, current_generation, error_data)

        # Enqueue scheduled outbox retry in the same atomic transaction
        outbox_row = TaskOutbox(
            id=uuid.uuid4(),
            task_id=task_id,
            queue_name=queue_name,
            payload={"task_id": str(task_id), "organization_id": row.organization_id, "case_id": row.case_id},
            status=OutboxStatus.PENDING.value,
            scheduled_for=scheduled_for,
            created_at=now,
            updated_at=now,
        )
        session.add(outbox_row)
        session.flush()

        AuditService.record_event(
            session,
            organization_id=row.organization_id,
            engine_name="task_manager",
            action="task_transient_retry",
            task_id=task_id,
            case_id=row.case_id,
            previous_state=TaskState.RUNNING.value,
            new_state=TaskState.RETRYING.value,
            lease_generation=current_generation,
            payload=error_data,
        )
        return True

    @classmethod
    def commit_task_permanent_failure(
        cls,
        session: Session,
        task_id: UUID,
        current_generation: int,
        error_data: dict[str, Any],
    ) -> bool:
        """Atomically transition task to FAILED with zero retries."""
        now = datetime.now(timezone.utc)
        stmt = (
            sa.update(Task)
            .where(
                Task.id == task_id,
                Task.lease_generation == current_generation,
                Task.state == TaskState.RUNNING.value,
            )
            .values(
                state=TaskState.FAILED.value,
                lease_expires_at=None,
                error_details=error_data,
                updated_at=now,
            )
            .returning(Task.organization_id, Task.case_id)
        )
        row = session.execute(stmt).first()
        if not row:
            raise StaleWorkerLeaseError(f"Lease generation {current_generation} revoked on permanent failure for task {task_id}")

        AuditService.record_event(
            session,
            organization_id=row.organization_id,
            engine_name="task_manager",
            action="task_permanent_failure",
            task_id=task_id,
            case_id=row.case_id,
            previous_state=TaskState.RUNNING.value,
            new_state=TaskState.FAILED.value,
            lease_generation=current_generation,
            payload=error_data,
        )
        return True

    @classmethod
    def commit_task_retry_exhaustion(
        cls,
        session: Session,
        task_id: UUID,
        current_generation: int,
        error_data: dict[str, Any],
    ) -> bool:
        """Atomically transition task to DEAD_LETTER upon exceeding retry limit."""
        now = datetime.now(timezone.utc)
        stmt = (
            sa.update(Task)
            .where(
                Task.id == task_id,
                Task.lease_generation == current_generation,
                Task.state == TaskState.RUNNING.value,
            )
            .values(
                state=TaskState.DEAD_LETTER.value,
                lease_expires_at=None,
                error_details=error_data,
                updated_at=now,
            )
            .returning(Task.organization_id, Task.case_id)
        )
        row = session.execute(stmt).first()
        if not row:
            raise StaleWorkerLeaseError(f"Lease generation {current_generation} revoked on DLQ transition for task {task_id}")

        AuditService.record_event(
            session,
            organization_id=row.organization_id,
            engine_name="task_manager",
            action="task_dead_lettered",
            task_id=task_id,
            case_id=row.case_id,
            previous_state=TaskState.RUNNING.value,
            new_state=TaskState.DEAD_LETTER.value,
            lease_generation=current_generation,
            payload=error_data,
        )
        return True

    @staticmethod
    def reclaim_stale_tasks(session: Session) -> list[UUID]:
        """Reap tasks where worker lease expired. Increments generation and schedules retry."""
        now = datetime.now(timezone.utc)
        expired_tasks = (
            session.query(Task)
            .filter(
                Task.state == TaskState.RUNNING.value,
                Task.lease_expires_at < now,
            )
            .with_for_update(skip_locked=True)
            .all()
        )

        reclaimed_ids = []
        for task in expired_tasks:
            if task.retry_count < task.max_retries:
                task.state = TaskState.RETRYING.value
                task.retry_count += 1
                task.lease_generation += 1
                task.lease_expires_at = None
                task.worker_id = None
                # Add outbox entry for retry
                session.add(
                    TaskOutbox(
                        id=uuid.uuid4(),
                        task_id=task.id,
                        queue_name="ring1_tasks",
                        payload={"task_id": str(task.id), "organization_id": task.organization_id, "case_id": task.case_id},
                        status=OutboxStatus.PENDING.value,
                    )
                )
            else:
                task.state = TaskState.DEAD_LETTER.value
                task.lease_generation += 1
                task.lease_expires_at = None
                task.worker_id = None
            reclaimed_ids.append(task.id)

        session.flush()
        return reclaimed_ids

    @staticmethod
    def replay_task(session: Session, original_task_id: UUID) -> tuple[Task, TaskOutbox]:
        """Create a new linked task replaying a dead-lettered or failed task.
        
        Preserves original task history and forensic audit records.
        """
        original_task = session.get(Task, original_task_id)
        if not original_task:
            raise ValueError(f"Task {original_task_id} not found")

        now = datetime.now(timezone.utc)
        new_task_id = uuid.uuid4()

        new_task = Task(
            id=new_task_id,
            organization_id=original_task.organization_id,
            case_id=original_task.case_id,
            user_id=original_task.user_id,
            task_type=original_task.task_type,
            state=TaskState.PENDING.value,
            payload=original_task.payload,
            correlation_id=original_task.correlation_id,
            replayed_from_task_id=original_task.id,
            created_at=now,
            updated_at=now,
        )
        session.add(new_task)

        original_task.replayed_to_task_id = new_task_id
        original_task.updated_at = now

        outbox_row = TaskOutbox(
            id=uuid.uuid4(),
            task_id=new_task_id,
            queue_name="ring1_tasks",
            payload={"task_id": str(new_task_id), "organization_id": new_task.organization_id, "case_id": new_task.case_id},
            status=OutboxStatus.PENDING.value,
            created_at=now,
            updated_at=now,
        )
        session.add(outbox_row)
        session.flush()

        AuditService.record_event(
            session,
            organization_id=new_task.organization_id,
            engine_name="task_manager",
            action="task_replayed",
            task_id=new_task_id,
            case_id=new_task.case_id,
            payload={"replayed_from": str(original_task_id)},
        )

        return new_task, outbox_row
