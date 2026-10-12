"""
Local filesystem implementation of RawStorageBackend.
"""
from pathlib import Path
import os

from orgbrain_ingest.ingestion.errors import StorageError
from orgbrain_ingest.storage.base import RawStorageBackend


class LocalStorageBackend(RawStorageBackend):
    """Local filesystem storage backend for raw documents.

    Keeps storage root configurable, isolates files from application code,
    and references objects exclusively via relative logical storage keys.
    """

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path).resolve()
        self._ensure_directory(self.base_path)

    @property
    def storage_mode(self) -> str:
        return "local"

    def _ensure_directory(self, path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(f"Failed to create storage directory {path}: {exc}") from exc

    def _resolve_and_validate_path(self, storage_key: str) -> Path:
        """Resolve storage key against base_path and guard against path traversal."""
        # Normalize forward slashes / strip leading slashes
        clean_key = storage_key.strip().replace("\\", "/").lstrip("/")
        if not clean_key:
            raise StorageError("Storage key cannot be empty")

        target_path = (self.base_path / clean_key).resolve()

        # Prevent directory traversal attacks
        if not str(target_path).startswith(str(self.base_path)):
            raise StorageError(f"Path traversal detected for storage key: {storage_key}")

        return target_path

    def store(self, content: bytes, destination_key: str) -> str:
        """Store raw content at destination_key.

        Returns the normalized logical storage_key (never leaking the host's absolute path).
        """
        # Normalize logical key
        normalized_key = destination_key.strip().replace("\\", "/").lstrip("/")
        target_path = self._resolve_and_validate_path(normalized_key)

        try:
            self._ensure_directory(target_path.parent)
            # Write to file
            temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
            temp_path.write_bytes(content)
            # Atomic replace where supported
            os.replace(temp_path, target_path)
            return normalized_key
        except Exception as exc:
            raise StorageError(f"Failed to store file at {normalized_key}: {exc}") from exc

    def retrieve(self, storage_key: str) -> bytes:
        """Retrieve raw bytes by logical storage_key."""
        target_path = self._resolve_and_validate_path(storage_key)

        if not target_path.exists() or not target_path.is_file():
            raise StorageError(f"Object not found for storage key: {storage_key}")

        try:
            return target_path.read_bytes()
        except Exception as exc:
            raise StorageError(f"Failed to read file from storage key {storage_key}: {exc}") from exc

    def exists(self, storage_key: str) -> bool:
        """Check whether object exists at storage_key."""
        try:
            target_path = self._resolve_and_validate_path(storage_key)
            return target_path.exists() and target_path.is_file()
        except StorageError:
            return False
