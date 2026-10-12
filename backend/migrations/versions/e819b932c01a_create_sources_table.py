"""create_sources_table

Revision ID: e819b932c01a
Revises: 778be99882b6
Create Date: 2026-10-12 08:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e819b932c01a"
down_revision: Union[str, Sequence[str], None] = "778be99882b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to create sources table."""
    op.create_table(
        "sources",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "source_type",
            sa.String(length=50),
            server_default=sa.text("'document'"),
            nullable=False,
        ),
        sa.Column(
            "storage_mode",
            sa.String(length=50),
            server_default=sa.text("'local'"),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(length=1000), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'ingested'"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_by",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("size_bytes > 0", name="ck_sources_size_bytes_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_sources_checksum_sha256",
        "sources",
        ["checksum_sha256"],
        unique=False,
    )
    op.create_index(
        "ix_sources_uploaded_by",
        "sources",
        ["uploaded_by"],
        unique=False,
    )
    op.create_index(
        "ix_sources_created_at",
        "sources",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema to drop sources table."""
    op.drop_index("ix_sources_created_at", table_name="sources")
    op.drop_index("ix_sources_uploaded_by", table_name="sources")
    op.drop_index("ix_sources_checksum_sha256", table_name="sources")
    op.drop_table("sources")
