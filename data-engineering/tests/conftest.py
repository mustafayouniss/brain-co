"""
Pytest configuration for Data Engineering test suite.
"""
from pathlib import Path
import sys
import pytest

# Ensure data-engineering root is in sys.path
_DE_DIR = Path(__file__).resolve().parent.parent
if str(_DE_DIR) not in sys.path:
    sys.path.insert(0, str(_DE_DIR))

from orgbrain_ingest.storage.local import LocalStorageBackend
from orgbrain_ingest.ingestion.validation import FileValidator
from orgbrain_ingest.ingestion.pipeline import IngestionPipeline


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to deterministic evaluation fixtures directory."""
    return _DE_DIR / "fixtures" / "ingestion"


@pytest.fixture
def local_storage(tmp_path: Path) -> LocalStorageBackend:
    """Isolated LocalStorageBackend using pytest tmp_path."""
    storage_root = tmp_path / "raw_storage"
    return LocalStorageBackend(storage_root)


@pytest.fixture
def default_validator() -> FileValidator:
    """Default FileValidator instance."""
    return FileValidator()


@pytest.fixture
def ingestion_pipeline(local_storage: LocalStorageBackend, default_validator: FileValidator) -> IngestionPipeline:
    """Ready-to-use IngestionPipeline with isolated local storage."""
    return IngestionPipeline(storage_backend=local_storage, validator=default_validator)
