"""create_tasks_outbox_audit_tables

Revision ID: a28b3c4d5e6f
Revises: f19a0a1b2c3d
Create Date: 2026-10-30 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a28b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "f19a0a1b2c3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tasks, task_outbox, and audit_events tables; alter observations."""
    # 1. tasks table
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(length=255), nullable=False),
        sa.Column("case_id", sa.String(length=255), nullable=True),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("task_type", sa.String(length=100), nullable=False, server_default=sa.text("'general_ingestion'")),
        sa.Column("state", sa.String(length=50), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        sa.Column("lease_generation", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column("replayed_from_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("replayed_to_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_org_state", "tasks", ["organization_id", "state"], unique=False)
    op.create_index("ix_tasks_case_id", "tasks", ["case_id"], unique=False)
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"], unique=False)
    op.create_index("ix_tasks_lease_expiry", "tasks", ["state", "lease_expires_at"], unique=False)
    op.create_index(
        "uq_tasks_org_idempotency",
        "tasks",
        ["organization_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    # 2. task_outbox table
    op.create_table(
        "task_outbox",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("queue_name", sa.String(length=100), nullable=False, server_default=sa.text("'ring1_tasks'")),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("dispatch_generation", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("dispatch_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("dispatch_lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_outbox_status_lease", "task_outbox", ["status", "dispatch_lease_expires_at"], unique=False)
    op.create_index("ix_task_outbox_task_id", "task_outbox", ["task_id"], unique=False)
    op.create_index("ix_task_outbox_created_at", "task_outbox", ["created_at"], unique=False)

    # 3. audit_events table
    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", sa.String(length=255), nullable=False),
        sa.Column("case_id", sa.String(length=255), nullable=True),
        sa.Column("actor_ref", sa.String(length=255), nullable=True),
        sa.Column("engine_name", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("previous_state", sa.String(length=50), nullable=True),
        sa.Column("new_state", sa.String(length=50), nullable=True),
        sa.Column("proposed_destination", sa.String(length=100), nullable=True),
        sa.Column("accepted_or_rejected", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("execution_attempt", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("lease_generation", sa.BigInteger(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("payload_checksum", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_task_id", "audit_events", ["task_id"], unique=False)
    op.create_index("ix_audit_events_org_created", "audit_events", ["organization_id", "created_at"], unique=False)
    op.create_index("ix_audit_events_engine_action", "audit_events", ["engine_name", "action"], unique=False)
    op.create_index("ix_audit_events_case_id", "audit_events", ["case_id"], unique=False)
    op.create_index("ix_audit_events_correlation", "audit_events", ["correlation_id"], unique=False)

    # 4. Alter ring1_observations: add nullable observation_type and expires_at
    op.add_column("ring1_observations", sa.Column("observation_type", sa.String(length=100), nullable=True))
    op.add_column("ring1_observations", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))

    # 5. Composite cursor index on ring1_observations using autocommit_block
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_ring1_observations_cursor",
            "ring1_observations",
            ["created_at", "id"],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    """Revert schema changes."""
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_ring1_observations_cursor",
            table_name="ring1_observations",
            postgresql_concurrently=True,
        )

    op.drop_column("ring1_observations", "expires_at")
    op.drop_column("ring1_observations", "observation_type")

    op.drop_table("audit_events")
    op.drop_table("task_outbox")
    op.drop_table("tasks")
