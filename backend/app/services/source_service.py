"""
Source registration service for PostgreSQL Source Memory.

Design conventions:
- Follows caller-owned commit pattern (D-014): this service only adds and flushes.
  The transaction boundary and final commit are owned by the API endpoint / caller.
- Integrates with IngestionResult from Data Engineering pipeline.
"""
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.models.source import Source


def create_source(
    db: Session,
    *,
    original_filename: str,
    content_type: str,
    size_bytes: int,
    checksum_sha256: str,
    storage_key: str,
    uploaded_by: uuid.UUID,
    source_id: uuid.UUID | None = None,
    source_type: str = "document",
    storage_mode: str = "local",
    status: str = "ingested",
) -> Source:
    """Create and flush a new Source record in PostgreSQL.

    Does NOT commit the transaction — caller commits.

    Parameters
    ----------
    db : Session
        Active database session.
    original_filename : str
        Original filename of the ingested document.
    content_type : str
        MIME content type.
    size_bytes : int
        File size in bytes.
    checksum_sha256 : str
        SHA-256 fingerprint.
    storage_key : str
        Logical key reference in raw storage.
    uploaded_by : uuid.UUID
        Foreign key reference to authenticated User (users.id).
    source_id : uuid.UUID, optional
        Pre-generated stable UUID (e.g. from ingestion pipeline).
    source_type : str, default 'document'
        Source classification.
    storage_mode : str, default 'local'
        Storage backend identifier.
    status : str, default 'ingested'
        Initial source lifecycle status.

    Returns
    -------
    Source
        The flushed Source ORM instance.
    """
    kwargs: dict[str, Any] = {
        "original_filename": original_filename,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "checksum_sha256": checksum_sha256,
        "storage_key": storage_key,
        "uploaded_by": uploaded_by,
        "source_type": source_type,
        "storage_mode": storage_mode,
        "status": status,
    }

    if source_id is not None:
        kwargs["id"] = source_id

    source = Source(**kwargs)
    db.add(source)
    db.flush()
    return source


def register_ingestion_result(
    db: Session,
    result: Any,
) -> Source:
    """Convenience helper to register an IngestionResult instance into PostgreSQL.

    Does NOT commit — caller commits.
    """
    return create_source(
        db,
        source_id=result.source_id,
        original_filename=result.original_filename,
        content_type=result.content_type,
        size_bytes=result.size_bytes,
        checksum_sha256=result.checksum_sha256,
        storage_key=result.storage_key,
        uploaded_by=result.uploaded_by,
        source_type=result.source_type,
        storage_mode=result.storage_mode,
    )
