"""
POST /api/v1/sources — Document ingestion endpoint.

Integration status:
- Implementation is complete and isolated.
- Mounting in app.api.v1.__init__ and importing get_current_user from app.api.deps
  is currently BLOCKED pending resolution of pre-existing Git merge conflicts.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.source import SourceResponse
from app.services.source_service import create_source

# Import Data Engineering components
from orgbrain_ingest.ingestion.errors import StorageError, ValidationError
from orgbrain_ingest.ingestion.pipeline import IngestionPipeline
from orgbrain_ingest.storage.local import LocalStorageBackend

router = APIRouter()

# Default raw storage directory (configurable)
_STORAGE_ROOT = Path("raw_storage").resolve()
_pipeline = IngestionPipeline(storage_backend=LocalStorageBackend(_STORAGE_ROOT))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SourceResponse,
    summary="Ingest raw source document",
)
async def ingest_source_endpoint(
    file: UploadFile = File(..., description="Raw document file (PDF or TXT)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SourceResponse:
    """Ingest a raw document file into Source Memory.

    Workflow:
    1. Read uploaded raw bytes.
    2. Data Engineering pipeline validates, fingerprints (SHA-256), and stores raw file.
    3. Register Source metadata row in PostgreSQL (linked to current_user.id).
    4. Backend transaction commit.
    5. Returns sanitized SourceResponse (no host paths or secrets exposed).
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    content = await file.read()

    try:
        # Run Data Engineering pipeline
        ingest_result = _pipeline.ingest(
            filename=file.filename,
            content=content,
            uploaded_by=current_user.id,
            content_type=file.content_type,
            source_type="document",
        )

        # Register in PostgreSQL (caller-owned commit)
        source = create_source(
            db,
            source_id=ingest_result.source_id,
            original_filename=ingest_result.original_filename,
            content_type=ingest_result.content_type,
            size_bytes=ingest_result.size_bytes,
            checksum_sha256=ingest_result.checksum_sha256,
            storage_key=ingest_result.storage_key,
            uploaded_by=current_user.id,
            source_type=ingest_result.source_type,
            storage_mode=ingest_result.storage_mode,
        )
        db.commit()
        db.refresh(source)

        return SourceResponse.model_validate(source)

    except ValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except StorageError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store raw source file",
        )
