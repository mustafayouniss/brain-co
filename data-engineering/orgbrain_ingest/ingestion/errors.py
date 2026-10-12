"""
Ingestion errors and exceptions.
"""


class IngestionError(Exception):
    """Base exception for all ingestion pipeline errors."""
    pass


class ValidationError(IngestionError):
    """Raised when file validation fails (type, size, empty, or format)."""
    pass


class StorageError(IngestionError):
    """Raised when writing or reading from raw storage fails."""
    pass
