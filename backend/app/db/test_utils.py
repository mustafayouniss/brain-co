"""
Test database safety utilities.

This module contains the authoritative safety guard used in BOTH the
test conftest.py fixtures AND the migration helper. It must never be
imported in production application code.
"""


def assert_safe_test_database(name: str, dev_db_name: str) -> None:
    """Raise RuntimeError unless *name* ends with '_test' and *name* != *dev_db_name*.

    This guard is the single enforcement point that prevents any test
    fixture or migration helper from accidentally operating on a
    development or production database.

    Args:
        name: The test database name to validate.
        dev_db_name: The development database name (e.g. settings.POSTGRES_DB).

    Raises:
        RuntimeError: If the name does not end with '_test' or equals dev_db_name.
    """
    if not name.endswith("_test"):
        raise RuntimeError(
            f"SAFETY GUARD: Database name {name!r} does not end with '_test'. "
            "Refusing to run test operations against a non-test database. "
            "Set POSTGRES_TEST_DB in .env to a name ending with '_test'."
        )
    if name == dev_db_name:
        raise RuntimeError(
            f"SAFETY GUARD: Database name {name!r} matches development database name {dev_db_name!r}. "
            "Refusing to run test operations against the development database."
        )
