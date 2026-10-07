"""
Test database safety utilities.

This module contains the authoritative safety guard used in BOTH the
test conftest.py fixtures AND the migration helper.  It must never be
imported in production application code.
"""


def assert_safe_test_database(name: str) -> None:
    """Raise RuntimeError unless *name* ends exactly with '_test'.

    This guard is the single enforcement point that prevents any test
    fixture or migration helper from accidentally operating on a
    development or production database.

    Args:
        name: The database name to validate.

    Raises:
        RuntimeError: If the name does not end with '_test'.
    """
    if not name.endswith("_test"):
        raise RuntimeError(
            f"SAFETY GUARD: Database name {name!r} does not end with '_test'. "
            "Refusing to run test operations against a non-test database. "
            "Set POSTGRES_TEST_DB in .env to a name ending with '_test'."
        )
