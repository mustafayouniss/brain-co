"""
Smoke test: proves that tests run against the isolated test database and
that the pgvector extension is present in it.
"""
from sqlalchemy import text


def test_db_isolation_and_vector_extension(db_session):
    """Verify we are connected to the test database, not the dev database.

    Asserts:
        1. current_database() ends with '_test' (safety contract).
        2. current_database() equals the configured POSTGRES_TEST_DB value.
        3. The 'vector' pgvector extension is present in the test database.
    """
    from app.core.config import settings

    # 1. What database are we actually connected to?
    current_db = db_session.execute(text("SELECT current_database()")).scalar()

    assert current_db.endswith("_test"), (
        f"Expected a test database (ending in '_test'), got {current_db!r}. "
        "The db_session fixture is connected to the wrong database."
    )
    assert current_db == settings.POSTGRES_TEST_DB, (
        f"Connected to {current_db!r} but POSTGRES_TEST_DB is "
        f"{settings.POSTGRES_TEST_DB!r}."
    )

    # 2. Is the vector extension present?
    ext = db_session.execute(
        text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    ).scalar()

    assert ext == "vector", (
        "The 'vector' (pgvector) extension was not found in the test database. "
        "Check that the migration ran successfully."
    )
