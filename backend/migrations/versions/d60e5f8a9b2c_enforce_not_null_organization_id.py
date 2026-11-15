"""Enforce NOT NULL constraint on organization_id for ring1_observations and ring1_memory_records.

Revision ID: d60e5f8a9b2c
Revises: c59d4e7f8a1b
Create Date: 2026-11-14 23:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d60e5f8a9b2c"
down_revision: Union[str, None] = "c59d4e7f8a1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Pre-check ring1_observations for NULL or whitespace-only organization_id
    obs_null_count = conn.execute(
        sa.text(
            "SELECT count(*) FROM ring1_observations "
            "WHERE organization_id IS NULL OR TRIM(organization_id) = ''"
        )
    ).scalar() or 0
    if obs_null_count > 0:
        raise RuntimeError(
            f"Cannot enforce NOT NULL on ring1_observations.organization_id: "
            f"found {obs_null_count} legacy rows with NULL or blank organization_id."
        )

    # Pre-check ring1_memory_records for NULL or whitespace-only organization_id
    mem_null_count = conn.execute(
        sa.text(
            "SELECT count(*) FROM ring1_memory_records "
            "WHERE organization_id IS NULL OR TRIM(organization_id) = ''"
        )
    ).scalar() or 0
    if mem_null_count > 0:
        raise RuntimeError(
            f"Cannot enforce NOT NULL on ring1_memory_records.organization_id: "
            f"found {mem_null_count} legacy rows with NULL or blank organization_id."
        )

    # 1. Alter ring1_observations.organization_id to NOT NULL
    op.alter_column(
        "ring1_observations",
        "organization_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    # 2. Alter ring1_memory_records.organization_id to NOT NULL
    op.alter_column(
        "ring1_memory_records",
        "organization_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )


def downgrade() -> None:
    # 1. Revert ring1_memory_records.organization_id to nullable
    op.alter_column(
        "ring1_memory_records",
        "organization_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )

    # 2. Revert ring1_observations.organization_id to nullable
    op.alter_column(
        "ring1_observations",
        "organization_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )
