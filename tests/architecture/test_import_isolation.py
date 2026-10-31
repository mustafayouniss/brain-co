"""Architecture isolation tests verifying strict boundary constraints via AST parsing."""

from __future__ import annotations

import ast
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GENERAL_BRAIN_DIR = REPO_ROOT / "brain" / "src" / "brain" / "general"
EXTENSIONS_DIR = REPO_ROOT / "brain" / "src" / "brain" / "extensions"

FORBIDDEN_GENERAL_IMPORTS = {
    "fastapi",
    "starlette",
    "sqlalchemy",
    "redis",
    "arq",
    "app",
    "backend",
    "ai",
    "brain.extensions",
}

FORBIDDEN_EXTENSION_IMPORTS = {
    "fastapi",
    "starlette",
    "sqlalchemy",
    "redis",
    "arq",
    "app",
    "backend",
    "ai",
}


def _get_imports_from_file(file_path: Path) -> list[str]:
    """Parse a Python source file into an AST and extract all top-level imported module names."""
    with open(file_path, "r", encoding="utf-8") as f:
        node = ast.parse(f.read(), filename=str(file_path))

    imported_names: list[str] = []
    for item in ast.walk(node):
        if isinstance(item, ast.Import):
            for alias in item.names:
                imported_names.append(alias.name)
        elif isinstance(item, ast.ImportFrom):
            if item.module:
                imported_names.append(item.module)
    return imported_names


def test_general_brain_strictly_isolated_from_forbidden_modules():
    """Verify that brain/src/brain/general/ NEVER imports Backend, DB, Redis, or Domain Extensions."""
    assert GENERAL_BRAIN_DIR.is_dir(), f"General brain directory not found: {GENERAL_BRAIN_DIR}"

    violations: list[str] = []
    for py_file in GENERAL_BRAIN_DIR.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        for imp in imports:
            for forbidden in FORBIDDEN_GENERAL_IMPORTS:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    rel_path = py_file.relative_to(REPO_ROOT)
                    violations.append(f"{rel_path}: imports '{imp}' (forbidden: '{forbidden}')")

    assert not violations, "General Brain boundary violations detected:\n" + "\n".join(violations)


def test_domain_extensions_strictly_isolated_from_backend_and_db():
    """Verify that brain/src/brain/extensions/ NEVER imports Backend, DB, Redis, or AI core."""
    assert EXTENSIONS_DIR.is_dir(), f"Extensions directory not found: {EXTENSIONS_DIR}"

    violations: list[str] = []
    for py_file in EXTENSIONS_DIR.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        for imp in imports:
            for forbidden in FORBIDDEN_EXTENSION_IMPORTS:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    rel_path = py_file.relative_to(REPO_ROOT)
                    violations.append(f"{rel_path}: imports '{imp}' (forbidden: '{forbidden}')")

    assert not violations, "Domain Extensions boundary violations detected:\n" + "\n".join(violations)
