"""Scope idempotency uniqueness to (organization_id, idempotency_key).

Revision ID: c59d4e7f8a1b
Revises: b39c4d5e6f7a
Create Date: 2026-11-14 22:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c59d4e7f8a1b"
down_revision: Union[str, None] = "b39c4d5e6f7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update ring1_observations idempotency index to composite (organization_id, idempotency_key)
    op.drop_index(
        "uq_ring1_observations_idempotency",
        table_name="ring1_observations",
    )
    op.create_index(
        "uq_ring1_observations_idempotency",
        "ring1_observations",
        ["organization_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    # 2. Update ring1_memory_records idempotency index to composite (organization_id, idempotency_key)
    op.drop_index(
        "uq_ring1_memory_records_idempotency",
        table_name="ring1_memory_records",
    )
    op.create_index(
        "uq_ring1_memory_records_idempotency",
        "ring1_memory_records",
        ["organization_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    # 1. Revert ring1_memory_records idempotency index
    op.drop_index(
        "uq_ring1_memory_records_idempotency",
        table_name="ring1_memory_records",
    )
    op.create_index(
        "uq_ring1_memory_records_idempotency",
        "ring1_memory_records",
        ["idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    # 2. Revert ring1_observations idempotency index
    op.drop_index(
        "uq_ring1_observations_idempotency",
        table_name="ring1_observations",
    )
    op.create_index(
        "uq_ring1_observations_idempotency",
        "ring1_observations",
        ["idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
