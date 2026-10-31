"""create_ring1_tables

Revision ID: f19a0a1b2c3d
Revises: e819b932c01a
Create Date: 2026-10-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f19a0a1b2c3d"
down_revision: Union[str, Sequence[str], None] = "e819b932c01a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to create Ring 1 observation and memory record tables."""
    # 1. ring1_observations table
    op.create_table(
        "ring1_observations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("actor_ref", sa.String(length=255), nullable=True),
        sa.Column("context_ref", sa.String(length=255), nullable=True),
        sa.Column("case_id", sa.String(length=255), nullable=True),
        sa.Column("organization_id", sa.String(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("trace_id", sa.String(length=255), nullable=True),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("idempotency_key", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'recorded'"),
            nullable=False,
        ),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_ring1_observations_event_type",
        "ring1_observations",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_ring1_observations_context_ref",
        "ring1_observations",
        ["context_ref"],
        unique=False,
    )
    op.create_index(
        "ix_ring1_observations_case_id",
        "ring1_observations",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_ring1_observations_trace_id",
        "ring1_observations",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        "uq_ring1_observations_idempotency",
        "ring1_observations",
        ["idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.create_index(
        "ix_ring1_observations_created_at",
        "ring1_observations",
        ["created_at"],
        unique=False,
    )

    # 2. ring1_memory_records table
    op.create_table(
        "ring1_memory_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("record_type", sa.String(length=100), nullable=False),
        sa.Column("context_ref", sa.String(length=255), nullable=True),
        sa.Column("case_id", sa.String(length=255), nullable=True),
        sa.Column("organization_id", sa.String(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("trace_id", sa.String(length=255), nullable=True),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("source_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
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

    op.create_index(
        "ix_ring1_memory_records_record_type",
        "ring1_memory_records",
        ["record_type"],
        unique=False,
    )
    op.create_index(
        "ix_ring1_memory_records_context_ref",
        "ring1_memory_records",
        ["context_ref"],
        unique=False,
    )
    op.create_index(
        "ix_ring1_memory_records_case_id",
        "ring1_memory_records",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_ring1_memory_records_trace_id",
        "ring1_memory_records",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        "uq_ring1_memory_records_idempotency",
        "ring1_memory_records",
        ["idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.create_index(
        "ix_ring1_memory_records_created_at",
        "ring1_memory_records",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema to remove Ring 1 tables."""
    op.drop_index("ix_ring1_memory_records_created_at", table_name="ring1_memory_records")
    op.drop_index("uq_ring1_memory_records_idempotency", table_name="ring1_memory_records")
    op.drop_index("ix_ring1_memory_records_trace_id", table_name="ring1_memory_records")
    op.drop_index("ix_ring1_memory_records_case_id", table_name="ring1_memory_records")
    op.drop_index("ix_ring1_memory_records_context_ref", table_name="ring1_memory_records")
    op.drop_index("ix_ring1_memory_records_record_type", table_name="ring1_memory_records")
    op.drop_table("ring1_memory_records")

    op.drop_index("ix_ring1_observations_created_at", table_name="ring1_observations")
    op.drop_index("uq_ring1_observations_idempotency", table_name="ring1_observations")
    op.drop_index("ix_ring1_observations_trace_id", table_name="ring1_observations")
    op.drop_index("ix_ring1_observations_case_id", table_name="ring1_observations")
    op.drop_index("ix_ring1_observations_context_ref", table_name="ring1_observations")
    op.drop_index("ix_ring1_observations_event_type", table_name="ring1_observations")
    op.drop_table("ring1_observations")
