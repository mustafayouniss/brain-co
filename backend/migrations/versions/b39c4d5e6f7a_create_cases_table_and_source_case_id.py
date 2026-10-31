"""Create cases table and add case_id and organization_id to sources.

Revision ID: b39c4d5e6f7a
Revises: a28b3c4d5e6f
Create Date: 2026-10-30 18:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "b39c4d5e6f7a"
down_revision: Union[str, None] = "a28b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create cases table
    op.create_table(
        "cases",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("case_number", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
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
        sa.UniqueConstraint("organization_id", "case_number", name="uq_cases_org_number"),
    )

    op.create_index("ix_cases_organization_id", "cases", ["organization_id"])
    op.create_index("ix_cases_case_number", "cases", ["case_number"])
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_created_at", "cases", ["created_at"])

    # 2. Add case_id and organization_id to sources
    op.add_column("sources", sa.Column("case_id", sa.String(128), nullable=True))
    op.add_column("sources", sa.Column("organization_id", sa.String(64), nullable=True))
    op.create_index("ix_sources_case_id", "sources", ["case_id"])
    op.create_index("ix_sources_organization_id", "sources", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_sources_organization_id", table_name="sources")
    op.drop_index("ix_sources_case_id", table_name="sources")
    op.drop_column("sources", "organization_id")
    op.drop_column("sources", "case_id")

    op.drop_index("ix_cases_created_at", table_name="cases")
    op.drop_index("ix_cases_status", table_name="cases")
    op.drop_index("ix_cases_case_number", table_name="cases")
    op.drop_index("ix_cases_organization_id", table_name="cases")
    op.drop_table("cases")
