"""
Guardrail test ensuring test files never directly instantiate connections
or reference the development database URL.
"""
from pathlib import Path

FORBIDDEN_PATTERNS = [
    "settings.DATABASE_URL",
    "create_engine(",
]

EXCLUDED_FILES = {
    "conftest.py",
    "test_no_raw_db_in_tests.py",
}


def scan_file_for_forbidden_patterns(file_path: Path) -> list[str]:
    """Scan a single python file for forbidden DB patterns."""
    violations = []
    content = file_path.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in content:
            violations.append(f"{file_path.name} contains forbidden pattern: {pattern!r}")
    return violations


def test_no_direct_database_url_or_create_engine_in_tests():
    """Scan all backend/tests/*.py (except excluded files) for forbidden DB patterns."""
    tests_dir = Path(__file__).resolve().parent
    all_violations = []

    for test_file in tests_dir.glob("*.py"):
        if test_file.name in EXCLUDED_FILES:
            continue
        all_violations.extend(scan_file_for_forbidden_patterns(test_file))

    assert not all_violations, (
        f"Found forbidden database access in test files:\n" + "\n".join(all_violations) +
        "\nTests must only use test_engine and db_session fixtures."
    )
