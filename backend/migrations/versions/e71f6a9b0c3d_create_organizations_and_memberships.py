"""Create organizations and organization_memberships tables with legacy migration.

Revision ID: e71f6a9b0c3d
Revises: d60e5f8a9b2c
Create Date: 2026-11-15 15:10:00.000000
"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e71f6a9b0c3d"
down_revision: Union[str, None] = "d60e5f8a9b2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False, server_default=sa.text("'legal'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_domain", "organizations", ["domain"], unique=False)
    op.create_index("ix_organizations_is_active", "organizations", ["is_active"], unique=False)

    # 2. Create organization_memberships table
    op.create_table(
        "organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", sa.String(length=100), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default=sa.text("'employee'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("role IN ('admin', 'employee')", name="ck_membership_role"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_membership_user"),
    )
    op.create_index("ix_org_membership_org_id", "organization_memberships", ["organization_id"], unique=False)
    op.create_index("ix_org_membership_user_id", "organization_memberships", ["user_id"], unique=False)

    # 3. Safe Legacy Data Migration
    conn = op.get_bind()

    # Seed default 'org-brain-corp' if not present
    existing_default = conn.execute(
        sa.text("SELECT id FROM organizations WHERE id = 'org-brain-corp'")
    ).fetchone()

    if not existing_default:
        conn.execute(
            sa.text(
                "INSERT INTO organizations (id, name, slug, domain, is_active, created_at, updated_at) "
                "VALUES ('org-brain-corp', 'Brain-Co', 'brain-corp', 'legal', true, now(), now())"
            )
        )

    # Backfill organizations referenced in cases table
    case_orgs = conn.execute(
        sa.text("SELECT DISTINCT organization_id FROM cases WHERE organization_id IS NOT NULL")
    ).fetchall()

    for row in case_orgs:
        c_org = row[0]
        if c_org:
            exists = conn.execute(
                sa.text("SELECT id FROM organizations WHERE id = :org_id"),
                {"org_id": c_org},
            ).fetchone()
            if not exists:
                slug = c_org.lower().replace("_", "-")
                conn.execute(
                    sa.text(
                        "INSERT INTO organizations (id, name, slug, domain, is_active, created_at, updated_at) "
                        "VALUES (:org_id, :name, :slug, 'legal', true, now(), now())"
                    ),
                    {"org_id": c_org, "name": f"Organization {c_org}", "slug": slug},
                )

    # Backfill existing users as members of 'org-brain-corp'
    existing_users = conn.execute(
        sa.text("SELECT id, role FROM users")
    ).fetchall()

    for u in existing_users:
        u_id, u_role = u[0], u[1]
        mem_exists = conn.execute(
            sa.text(
                "SELECT id FROM organization_memberships "
                "WHERE organization_id = 'org-brain-corp' AND user_id = :u_id"
            ),
            {"u_id": u_id},
        ).fetchone()

        if not mem_exists:
            conn.execute(
                sa.text(
                    "INSERT INTO organization_memberships (id, organization_id, user_id, role, is_active, created_at) "
                    "VALUES (gen_random_uuid(), 'org-brain-corp', :u_id, :role, true, now())"
                ),
                {"u_id": u_id, "role": u_role if u_role in ("admin", "employee") else "employee"},
            )


def downgrade() -> None:
    op.drop_index("ix_org_membership_user_id", table_name="organization_memberships")
    op.drop_index("ix_org_membership_org_id", table_name="organization_memberships")
    op.drop_table("organization_memberships")
    op.drop_index("ix_organizations_is_active", table_name="organizations")
    op.drop_index("ix_organizations_domain", table_name="organizations")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
