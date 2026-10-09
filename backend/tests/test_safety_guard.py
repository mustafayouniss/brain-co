"""
Unit tests for the assert_safe_test_database() safety guard.

These tests deliberately do NOT use the db_session fixture; they are
pure-Python unit tests that require no database connection.
"""
import pytest

from app.db.test_utils import assert_safe_test_database


class TestAssertSafeTestDatabase:
    """Tests for the single authoritative safety guard function."""

    # --- names that MUST pass (no exception) ---

    def test_canonical_test_db_name_passes(self):
        """The standard project test DB name must be accepted when distinct from dev."""
        # Should not raise
        assert_safe_test_database("orgbrain_legal_test", "orgbrain_legal")

    # --- names that MUST be refused (RuntimeError) ---

    def test_dev_db_name_refused(self):
        """The production/dev database name must be refused."""
        with pytest.raises(RuntimeError, match="SAFETY GUARD"):
            assert_safe_test_database("orgbrain_legal", "orgbrain_legal")

    def test_postgres_maintenance_db_refused(self):
        """The postgres maintenance database must be refused."""
        with pytest.raises(RuntimeError, match="SAFETY GUARD"):
            assert_safe_test_database("postgres", "orgbrain_legal")

    def test_empty_string_refused(self):
        """An empty string must be refused."""
        with pytest.raises(RuntimeError, match="SAFETY GUARD"):
            assert_safe_test_database("", "orgbrain_legal")

    def test_name_ending_in_test_old_refused(self):
        """'orgbrain_legal_test_old' ends in '_old', not '_test' — refused."""
        with pytest.raises(RuntimeError, match="SAFETY GUARD"):
            assert_safe_test_database("orgbrain_legal_test_old", "orgbrain_legal")

    def test_test_name_matching_dev_db_name_refused(self):
        """Even if name ends with '_test', it must be refused if it matches dev DB name."""
        with pytest.raises(RuntimeError, match="matches development database"):
            assert_safe_test_database("orgbrain_legal_test", "orgbrain_legal_test")
