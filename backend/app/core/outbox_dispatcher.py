"""Transactional Outbox Dispatcher for Ring 1.

Responsible for claiming outbox rows, enforcing dispatch generation fencing,
and acknowledging broker delivery without holding database locks during network calls.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.task import OutboxStatus, Task, TaskOutbox, TaskState


class OutboxDispatcher:
    """Manages transactional outbox claim, ACK, and retry lifecycle."""

    @staticmethod
    def claim_pending_records(
        session: Session,
        limit: int = 50,
        lease_seconds: int = 30,
    ) -> list[tuple[UUID, UUID, str, dict, int]]:
        """Phase 1: Claim pending or expired dispatching outbox rows in a short DB transaction.
        
        Atomically transitions task to QUEUED and outbox to DISPATCHING with incremented generation.
        Returns: list of (outbox_id, task_id, queue_name, payload, dispatch_generation).
        """
        now = datetime.now(timezone.utc)
        lease_expires_at = now + timedelta(seconds=lease_seconds)

        # Select records eligible for dispatch
        claimed_rows = (
            session.query(TaskOutbox)
            .filter(
                sa.or_(
                    TaskOutbox.status == OutboxStatus.PENDING.value,
                    sa.and_(
                        TaskOutbox.status == OutboxStatus.DISPATCHING.value,
                        TaskOutbox.dispatch_lease_expires_at < now,
                    ),
                ),
                sa.or_(
                    TaskOutbox.scheduled_for.is_(None),
                    TaskOutbox.scheduled_for <= now,
                ),
            )
            .order_by(TaskOutbox.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
            .all()
        )

        results = []
        for outbox in claimed_rows:
            outbox.status = OutboxStatus.DISPATCHING.value
            outbox.dispatch_generation += 1
            outbox.dispatch_lease_expires_at = lease_expires_at
            outbox.dispatch_attempts += 1
            outbox.updated_at = now

            # Ensure associated task is transitioned to QUEUED if still PENDING
            session.execute(
                sa.update(Task)
                .where(
                    Task.id == outbox.task_id,
                    Task.state == TaskState.PENDING.value,
                )
                .values(state=TaskState.QUEUED.value, updated_at=now)
            )

            results.append((outbox.id, outbox.task_id, outbox.queue_name, outbox.payload, outbox.dispatch_generation))

        session.flush()
        return results

    @staticmethod
    def acknowledge_dispatch(
        session: Session,
        outbox_id: UUID,
        claimed_dispatch_generation: int,
    ) -> bool:
        """Phase 3: Acknowledge successful broker enqueueing strictly verifying generation and DISPATCHING status."""
        now = datetime.now(timezone.utc)
        stmt = (
            sa.update(TaskOutbox)
            .where(
                TaskOutbox.id == outbox_id,
                TaskOutbox.status == OutboxStatus.DISPATCHING.value,
                TaskOutbox.dispatch_generation == claimed_dispatch_generation,
            )
            .values(
                status=OutboxStatus.DISPATCHED.value,
                dispatched_at=now,
                dispatch_lease_expires_at=None,
                updated_at=now,
            )
            .returning(TaskOutbox.id)
        )
        acked = session.execute(stmt).scalar_one_or_none()
        return acked is not None

    @staticmethod
    def record_terminal_dispatch_failure(
        session: Session,
        outbox_id: UUID,
        task_id: UUID,
        claimed_dispatch_generation: int,
        max_attempts: int = 5,
    ) -> bool:
        """Mark outbox as FAILED_DISPATCH when retries exhausted, fencing against stale dispatchers.
        
        Only marks task as FAILED if still in PENDING or QUEUED state; active/completed tasks are untouched.
        """
        now = datetime.now(timezone.utc)
        outbox_stmt = (
            sa.update(TaskOutbox)
            .where(
                TaskOutbox.id == outbox_id,
                TaskOutbox.status == OutboxStatus.DISPATCHING.value,
                TaskOutbox.dispatch_generation == claimed_dispatch_generation,
                TaskOutbox.dispatch_attempts >= max_attempts,
            )
            .values(
                status=OutboxStatus.FAILED_DISPATCH.value,
                dispatch_lease_expires_at=None,
                updated_at=now,
            )
            .returning(TaskOutbox.id)
        )
        updated_outbox = session.execute(outbox_stmt).scalar_one_or_none()
        if not updated_outbox:
            return False

        # Conditionally mark task FAILED only if not already claimed by a worker
        session.execute(
            sa.update(Task)
            .where(
                Task.id == task_id,
                Task.state.in_([TaskState.PENDING.value, TaskState.QUEUED.value]),
            )
            .values(
                state=TaskState.FAILED.value,
                error_details={"code": "DISPATCH_EXHAUSTED", "message": f"Broker enqueueing failed after {max_attempts} attempts"},
                updated_at=now,
            )
        )
        return True

    @staticmethod
    def admin_retry_outbox(
        session: Session,
        outbox_id: UUID,
    ) -> bool:
        """Admin manual retry: transitions FAILED_DISPATCH -> PENDING, increments generation to invalidate stale dispatchers, and reconciles Task state if failed from dispatch exhaustion."""
        now = datetime.now(timezone.utc)
        stmt = (
            sa.update(TaskOutbox)
            .where(
                TaskOutbox.id == outbox_id,
                TaskOutbox.status == OutboxStatus.FAILED_DISPATCH.value,
            )
            .values(
                status=OutboxStatus.PENDING.value,
                dispatch_generation=TaskOutbox.dispatch_generation + 1,
                dispatch_attempts=0,
                dispatch_lease_expires_at=None,
                updated_at=now,
            )
            .returning(TaskOutbox.id, TaskOutbox.task_id)
        )
        row = session.execute(stmt).first()
        if not row:
            return False

        # Reconcile associated Task state if it failed due to dispatch exhaustion
        session.execute(
            sa.update(Task)
            .where(
                Task.id == row.task_id,
                Task.state == TaskState.FAILED.value,
            )
            .values(
                state=TaskState.PENDING.value,
                error_details=None,
                updated_at=now,
            )
        )
        return True
