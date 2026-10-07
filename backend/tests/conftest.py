"""
Test configuration and shared fixtures for the OrgBrain backend test suite.

Safety guarantee
----------------
This file refuses to run against any database whose name does not end with
'_test'.  The check is enforced by assert_safe_test_database(), which is the
single authoritative guard used both here and inside the Alembic migration
helper, so the guarantee holds even if a caller bypasses the fixtures.

Fixture lifecycle
-----------------
* test_engine  (session scope)
  - Validates the test-DB name via the safety guard.
  - Creates the test database if it does not already exist.
  - Runs `alembic upgrade head` against it (NOT create_all).
  - Yields a SQLAlchemy Engine pointing at the test database.
  - The engine is disposed after all tests finish.

* db_session  (function scope)
  - Opens a connection from test_engine.
  - Starts an outer transaction that is NEVER committed.
  - Binds a Session with join_transaction_mode="create_savepoint" so that
    any SAVEPOINT usage inside the test is still rolled back with the outer
    transaction.
  - Yields the Session.
  - Teardown: close session → rollback outer transaction → close connection.
  - Each test therefore starts with a clean slate; the test database itself
    accumulates no data between runs.
"""

from pathlib import Path

import pytest
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.test_utils import assert_safe_test_database

# ---------------------------------------------------------------------------
# Absolute path to alembic.ini — works regardless of the CWD at invocation.
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_maintenance_url() -> str:
    """URL for the server-level 'postgres' maintenance database.

    We need this to CREATE the test database; we must connect to a database
    that already exists (postgres) before the target database exists.
    """
    return (
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/postgres"
    )


def _ensure_test_database_exists(db_name: str) -> None:
    """Create the test database if it does not yet exist.

    Uses AUTOCOMMIT so that CREATE DATABASE is not wrapped in a transaction
    (Postgres forbids transactional DDL for CREATE DATABASE).
    """
    maintenance_engine = create_engine(
        _build_maintenance_url(),
        isolation_level="AUTOCOMMIT",
    )
    try:
        with maintenance_engine.connect() as conn:
            row = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).fetchone()
            if row is None:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        maintenance_engine.dispose()


def _run_migrations(test_db_url: str) -> None:
    """Run `alembic upgrade head` against the test database.

    The URL is injected via config.attributes["database_url"] — an explicit
    marker that env.py checks.  When this key is absent (all normal alembic
    CLI invocations) env.py falls back to settings.DATABASE_URL, so the
    development database is never touched by the CLI.
    """
    cfg = AlembicConfig(str(_ALEMBIC_INI))
    cfg.attributes["database_url"] = test_db_url
    alembic_command.upgrade(cfg, "head")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_engine():
    """Session-scoped Engine pointing at the isolated test database.

    Validates naming, provisions the DB, and migrates it before the first
    test runs.  Disposes the engine after all tests finish.
    """
    db_name = settings.POSTGRES_TEST_DB

    # SAFETY GUARD — refuse if the name does not end with '_test' or matches dev DB.
    assert_safe_test_database(db_name, settings.POSTGRES_DB)

    _ensure_test_database_exists(db_name)
    _run_migrations(settings.TEST_DATABASE_URL)

    engine = create_engine(settings.TEST_DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Function-scoped Session that rolls back after every test.

    The outer transaction is never committed, so each test starts clean.
    """
    with test_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()
