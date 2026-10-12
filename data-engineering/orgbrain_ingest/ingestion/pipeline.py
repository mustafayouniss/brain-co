"""
Ingestion Pipeline orchestration for raw source documents.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import uuid
from typing import Callable, Any

from orgbrain_ingest.ingestion.checksum import calculate_sha256
from orgbrain_ingest.ingestion.validation import FileValidator
from orgbrain_ingest.storage.base import RawStorageBackend


@dataclass(frozen=True)
class IngestionResult:
    """Immutable data record resulting from raw file ingestion."""
    source_id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    storage_mode: str
    storage_key: str
    source_type: str
    uploaded_by: uuid.UUID


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and unsafe characters."""
    # Extract only the base name (strip any leading directory paths)
    base = Path(filename).name.strip()
    # Replace unsafe characters with underscores, keeping letters, numbers, dots, dashes, underscores
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return sanitized or "unnamed_source"


class IngestionPipeline:
    """Orchestrates validation, SHA-256 fingerprinting, raw storage, and source preparation."""

    def __init__(
        self,
        storage_backend: RawStorageBackend,
        validator: FileValidator | None = None,
    ) -> None:
        self.storage = storage_backend
        self.validator = validator or FileValidator()

    def ingest(
        self,
        *,
        filename: str,
        content: bytes,
        uploaded_by: uuid.UUID,
        content_type: str | None = None,
        source_type: str = "document",
    ) -> IngestionResult:
        """Execute the ingestion pipeline on raw file bytes.

        Steps:
        1. Validate filename, size, content-type
        2. Calculate SHA-256 fingerprint
        3. Generate stable UUID primary key
        4. Construct logical storage key
        5. Store raw bytes in storage backend
        6. Return IngestionResult

        Raises
        ------
        ValidationError
            If input fails policy validation.
        StorageError
            If raw storage write fails.
        """
        # 1. Validation
        self.validator.validate(filename=filename, content=content, content_type=content_type)

        # 2. Checksum calculation
        checksum = calculate_sha256(content)

        # 3. Stable identity generation
        source_id = uuid.uuid4()

        # 4. Storage key construction: sources/<source_id>/<safe_filename>
        safe_name = _sanitize_filename(filename)
        storage_key = f"sources/{source_id}/{safe_name}"

        # 5. Store raw bytes
        stored_key = self.storage.store(content=content, destination_key=storage_key)

        # Determine effective content type
        effective_ct = content_type or (
            "application/pdf" if filename.lower().endswith(".pdf") else "text/plain"
        )

        return IngestionResult(
            source_id=source_id,
            original_filename=Path(filename).name,
            content_type=effective_ct,
            size_bytes=len(content),
            checksum_sha256=checksum,
            storage_mode=self.storage.storage_mode,
            storage_key=stored_key,
            source_type=source_type,
            uploaded_by=uploaded_by,
        )

    def ingest_and_register(
        self,
        *,
        filename: str,
        content: bytes,
        uploaded_by: uuid.UUID,
        register_fn: Callable[[IngestionResult], Any],
        content_type: str | None = None,
        source_type: str = "document",
    ) -> Any:
        """Ingest raw file and invoke register_fn to coordinate registration.

        Caller maintains transaction boundary (caller-owned commit).
        """
        result = self.ingest(
            filename=filename,
            content=content,
            uploaded_by=uploaded_by,
            content_type=content_type,
            source_type=source_type,
        )
        return register_fn(result)
