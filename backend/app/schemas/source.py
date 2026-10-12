"""
Pydantic schemas for Source entities.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SourceResponse(BaseModel):
    """Client-facing representation of an ingested Source entity.

    Adheres to information hiding principles:
    - Exposes stable identity, filename, MIME type, size, checksum, status, and creation time.
    - NEVER exposes absolute filesystem paths, internal storage keys, or raw byte streams.
    """

    id: UUID = Field(..., description="Stable unique identifier for the source")
    original_filename: str = Field(..., description="Original name of the ingested file")
    content_type: str = Field(..., description="MIME content type of the file")
    size_bytes: int = Field(..., description="File size in bytes")
    checksum_sha256: str = Field(..., description="SHA-256 integrity checksum")
    source_type: str = Field(..., description="Source classification type (e.g. document)")
    status: str = Field(..., description="Current lifecycle status of the source")
    created_at: datetime = Field(..., description="Timestamp when the source was ingested")

    model_config = ConfigDict(from_attributes=True)
