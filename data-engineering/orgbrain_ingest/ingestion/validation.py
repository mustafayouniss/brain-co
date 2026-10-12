"""
File validation policy for Foundational Source Ingestion (V1).
"""
from pathlib import Path
from typing import Set

from orgbrain_ingest.ingestion.errors import ValidationError

# V1 Supported types
DEFAULT_ALLOWED_CONTENT_TYPES: Set[str] = {
    "application/pdf",
    "text/plain",
}

DEFAULT_ALLOWED_EXTENSIONS: Set[str] = {
    ".pdf",
    ".txt",
}

# 50 MB default maximum limit
DEFAULT_MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024


class FileValidator:
    """Validates raw source files against V1 ingestion policy."""

    def __init__(
        self,
        allowed_content_types: Set[str] | None = None,
        allowed_extensions: Set[str] | None = None,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    ) -> None:
        self.allowed_content_types = (
            allowed_content_types
            if allowed_content_types is not None
            else DEFAULT_ALLOWED_CONTENT_TYPES
        )
        self.allowed_extensions = (
            allowed_extensions
            if allowed_extensions is not None
            else DEFAULT_ALLOWED_EXTENSIONS
        )
        self.max_file_size_bytes = max_file_size_bytes

    def validate(
        self,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> None:
        """Validate filename, content bytes, and content_type.

        Raises
        ------
        ValidationError
            If any policy check fails.
        """
        # 1. Filename validation
        if not filename or not filename.strip():
            raise ValidationError("Filename cannot be empty")

        cleaned_name = filename.strip()
        ext = Path(cleaned_name).suffix.lower()

        if not ext:
            raise ValidationError(f"Filename '{cleaned_name}' must have an extension")

        if ext not in self.allowed_extensions:
            raise ValidationError(
                f"File extension '{ext}' is not supported. "
                f"Allowed extensions: {sorted(self.allowed_extensions)}"
            )

        # 2. Content size validation
        if content is None or len(content) == 0:
            raise ValidationError("File is empty (0 bytes). Empty files cannot be ingested.")

        size = len(content)
        if size > self.max_file_size_bytes:
            raise ValidationError(
                f"File size ({size} bytes) exceeds maximum allowed size "
                f"({self.max_file_size_bytes} bytes)"
            )

        # 3. Content-Type validation
        if content_type is not None:
            normalized_ct = content_type.strip().lower().split(";")[0].strip()
            if normalized_ct not in self.allowed_content_types:
                raise ValidationError(
                    f"Content type '{normalized_ct}' is not supported. "
                    f"Allowed types: {sorted(self.allowed_content_types)}"
                )
