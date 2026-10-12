"""
Tests for IngestionPipeline orchestration.
"""
from pathlib import Path
import uuid
import pytest

from orgbrain_ingest.ingestion.errors import ValidationError
from orgbrain_ingest.ingestion.pipeline import IngestionPipeline, IngestionResult
from orgbrain_ingest.storage.local import LocalStorageBackend


def test_pipeline_ingest_valid_file(
    ingestion_pipeline: IngestionPipeline,
    local_storage: LocalStorageBackend,
    fixtures_dir: Path,
):
    pdf_path = fixtures_dir / "valid_small.pdf"
    content = pdf_path.read_bytes()
    user_id = uuid.uuid4()

    result: IngestionResult = ingestion_pipeline.ingest(
        filename="Contract_2026.pdf",
        content=content,
        uploaded_by=user_id,
        content_type="application/pdf",
        source_type="document",
    )

    # 1. Result attributes verification
    assert isinstance(result.source_id, uuid.UUID)
    assert result.original_filename == "Contract_2026.pdf"
    assert result.content_type == "application/pdf"
    assert result.size_bytes == len(content)
    assert len(result.checksum_sha256) == 64
    assert result.storage_mode == "local"
    assert result.uploaded_by == user_id
    assert result.source_type == "document"

    # 2. Key format: sources/{source_id}/{safe_filename}
    assert result.storage_key == f"sources/{result.source_id}/Contract_2026.pdf"

    # 3. Storage byte fidelity
    stored_bytes = local_storage.retrieve(result.storage_key)
    assert stored_bytes == content


def test_pipeline_sanitizes_filename(
    ingestion_pipeline: IngestionPipeline,
):
    content = b"Some valid plain text document content."
    user_id = uuid.uuid4()

    # Filename with path traversal attempts
    result = ingestion_pipeline.ingest(
        filename="../../etc/passwd.txt",
        content=content,
        uploaded_by=user_id,
        content_type="text/plain",
    )

    assert result.original_filename == "passwd.txt"
    assert ".." not in result.storage_key
    assert result.storage_key == f"sources/{result.source_id}/passwd.txt"


def test_pipeline_rejects_empty_file(
    ingestion_pipeline: IngestionPipeline,
    fixtures_dir: Path,
):
    empty_bytes = (fixtures_dir / "empty.pdf").read_bytes()
    with pytest.raises(ValidationError, match="empty \\(0 bytes\\)"):
        ingestion_pipeline.ingest(
            filename="empty.pdf",
            content=empty_bytes,
            uploaded_by=uuid.uuid4(),
            content_type="application/pdf",
        )


def test_pipeline_rejects_unsupported_file(
    ingestion_pipeline: IngestionPipeline,
    fixtures_dir: Path,
):
    xyz_bytes = (fixtures_dir / "unsupported_file.xyz").read_bytes()
    with pytest.raises(ValidationError, match="not supported"):
        ingestion_pipeline.ingest(
            filename="sample.xyz",
            content=xyz_bytes,
            uploaded_by=uuid.uuid4(),
        )


def test_pipeline_ingest_and_register(
    ingestion_pipeline: IngestionPipeline,
):
    content = b"Content for registration callback testing."
    user_id = uuid.uuid4()
    registered_records = []

    def fake_register(res: IngestionResult):
        record = {
            "id": res.source_id,
            "key": res.storage_key,
            "user": res.uploaded_by,
        }
        registered_records.append(record)
        return record

    output = ingestion_pipeline.ingest_and_register(
        filename="statement.txt",
        content=content,
        uploaded_by=user_id,
        register_fn=fake_register,
    )

    assert len(registered_records) == 1
    assert output["id"] == registered_records[0]["id"]
    assert output["user"] == user_id
