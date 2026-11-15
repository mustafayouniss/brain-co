"""Create mesh_events, ws_tickets, and case_assignments tables.

Revision ID: f82a1b3c4d5e
Revises: e71f6a9b0c3d
Create Date: 2026-11-15 17:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f82a1b3c4d5e"
down_revision: Union[str, None] = "e71f6a9b0c3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ws_tickets table for atomic, multi-worker single-use WebSocket tickets
    op.create_table(
        "ws_tickets",
        sa.Column("ticket_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.String(length=100), nullable=False),
        sa.Column("case_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ticket_hash"),
    )
    op.create_index("ix_ws_tickets_consumed_expires", "ws_tickets", ["consumed", "expires_at"], unique=False)
    op.create_index("ix_ws_tickets_org_user", "ws_tickets", ["organization_id", "user_id"], unique=False)

    # 2. Create case_assignments table for explicit case access control (CACS)
    op.create_table(
        "case_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "user_id", name="uq_case_assignment_case_user"),
    )
    op.create_index("ix_case_assignments_case_id", "case_assignments", ["case_id"], unique=False)
    op.create_index("ix_case_assignments_user_id", "case_assignments", ["user_id"], unique=False)

    # 3. Create mesh_events table for durable, ordered, case-isolated mesh execution telemetry
    op.create_table(
        "mesh_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.BigInteger(), nullable=False),
        sa.Column("organization_id", sa.String(length=100), nullable=False),
        sa.Column("case_id", sa.String(length=100), nullable=True),
        sa.Column("source_engine", sa.String(length=50), nullable=False),
        sa.Column("destination_engine", sa.String(length=50), nullable=True),
        sa.Column("capability", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("plan_version", sa.Integer(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mesh_events_org_case_seq", "mesh_events", ["organization_id", "case_id", "sequence_number"], unique=False)
    op.create_index("ix_mesh_events_run_seq", "mesh_events", ["run_id", "sequence_number"], unique=False)
    op.create_index("ix_mesh_events_created_at", "mesh_events", ["created_at"], unique=False)


def downgrade() -> None:
    # 3. Drop mesh_events table and indexes
    op.drop_index("ix_mesh_events_created_at", table_name="mesh_events")
    op.drop_index("ix_mesh_events_run_seq", table_name="mesh_events")
    op.drop_index("ix_mesh_events_org_case_seq", table_name="mesh_events")
    op.drop_table("mesh_events")

    # 2. Drop case_assignments table and indexes
    op.drop_index("ix_case_assignments_user_id", table_name="case_assignments")
    op.drop_index("ix_case_assignments_case_id", table_name="case_assignments")
    op.drop_table("case_assignments")

    # 1. Drop ws_tickets table and indexes
    op.drop_index("ix_ws_tickets_org_user", table_name="ws_tickets")
    op.drop_index("ix_ws_tickets_consumed_expires", table_name="ws_tickets")
    op.drop_table("ws_tickets")
