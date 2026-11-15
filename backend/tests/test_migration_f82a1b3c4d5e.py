"""Test Alembic Migration f82a1b3c4d5e: Mesh Events, WS Tickets, Case Assignments.

Verifies:
1. Upgrade behavior creating ws_tickets, case_assignments, mesh_events.
2. Downgrade behavior cleanly removing the tables and indexes.
3. Re-upgrade cleanly idempotently.
4. Preservation of existing tables and schemas.
"""

from pathlib import Path
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
import pytest
from sqlalchemy import inspect, text

from app.core.config import settings
from app.db.test_utils import assert_safe_test_database

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"


def test_migration_f82a1b3c4d5e_upgrade_and_downgrade(test_engine):
    """Verify upgrade and downgrade cycle for revision f82a1b3c4d5e on test DB."""
    test_db_name = settings.POSTGRES_TEST_DB
    assert_safe_test_database(test_db_name, settings.POSTGRES_DB)

    test_db_url = settings.TEST_DATABASE_URL

    alembic_cfg = AlembicConfig(str(_ALEMBIC_INI))
    alembic_cfg.attributes["database_url"] = test_db_url

    # 1. Upgrade to head (f82a1b3c4d5e)
    alembic_command.upgrade(alembic_cfg, "head")

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    assert "ws_tickets" in tables, "ws_tickets table must be present after upgrade"
    assert "case_assignments" in tables, "case_assignments table must be present after upgrade"
    assert "mesh_events" in tables, "mesh_events table must be present after upgrade"
    assert "organizations" in tables, "Existing organizations table must be preserved"
    assert "cases" in tables, "Existing cases table must be preserved"

    # Verify ws_tickets indexes
    ws_ticket_indexes = {idx["name"]: idx["column_names"] for idx in inspector.get_indexes("ws_tickets")}
    assert "ix_ws_tickets_consumed_expires" in ws_ticket_indexes
    assert "ix_ws_tickets_org_user" in ws_ticket_indexes

    # Verify case_assignments constraints & indexes
    case_assign_indexes = {idx["name"]: idx["column_names"] for idx in inspector.get_indexes("case_assignments")}
    assert "ix_case_assignments_case_id" in case_assign_indexes
    assert "ix_case_assignments_user_id" in case_assign_indexes

    # Verify mesh_events indexes
    mesh_indexes = {idx["name"]: idx["column_names"] for idx in inspector.get_indexes("mesh_events")}
    assert "ix_mesh_events_org_case_seq" in mesh_indexes
    assert "ix_mesh_events_run_seq" in mesh_indexes
    assert "ix_mesh_events_created_at" in mesh_indexes

    # 2. Downgrade -1 (back to e71f6a9b0c3d)
    alembic_command.downgrade(alembic_cfg, "e71f6a9b0c3d")

    inspector_down = inspect(test_engine)
    down_tables = inspector_down.get_table_names()
    assert "ws_tickets" not in down_tables, "ws_tickets must be dropped on downgrade"
    assert "case_assignments" not in down_tables, "case_assignments must be dropped on downgrade"
    assert "mesh_events" not in down_tables, "mesh_events must be dropped on downgrade"
    assert "organizations" in down_tables, "organizations must remain after downgrade"
    assert "cases" in down_tables, "cases must remain after downgrade"

    # 3. Re-upgrade to head (f82a1b3c4d5e) to leave test DB in target state
    alembic_command.upgrade(alembic_cfg, "head")

    inspector_reup = inspect(test_engine)
    reup_tables = inspector_reup.get_table_names()
    assert "ws_tickets" in reup_tables
    assert "case_assignments" in reup_tables
    assert "mesh_events" in reup_tables
