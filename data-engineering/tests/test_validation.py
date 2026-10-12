"""
Tests for file validation policy in Data Engineering.
"""
from pathlib import Path
import pytest

from orgbrain_ingest.ingestion.errors import ValidationError
from orgbrain_ingest.ingestion.validation import FileValidator


def test_valid_pdf_accepted(default_validator: FileValidator, fixtures_dir: Path):
    pdf_bytes = (fixtures_dir / "valid_small.pdf").read_bytes()
    # Should not raise
    default_validator.validate("test_doc.pdf", pdf_bytes, "application/pdf")


def test_valid_txt_accepted(default_validator: FileValidator, fixtures_dir: Path):
    txt_bytes = (fixtures_dir / "valid_small.txt").read_bytes()
    # Should not raise
    default_validator.validate("contract.txt", txt_bytes, "text/plain")


def test_valid_txt_with_charset_accepted(default_validator: FileValidator):
    default_validator.validate("doc.txt", b"sample content", "text/plain; charset=utf-8")


def test_empty_filename_rejected(default_validator: FileValidator):
    with pytest.raises(ValidationError, match="Filename cannot be empty"):
        default_validator.validate("", b"some content")

    with pytest.raises(ValidationError, match="Filename cannot be empty"):
        default_validator.validate("   ", b"some content")


def test_missing_extension_rejected(default_validator: FileValidator):
    with pytest.raises(ValidationError, match="must have an extension"):
        default_validator.validate("sample_file", b"some content")


def test_unsupported_extension_rejected(default_validator: FileValidator, fixtures_dir: Path):
    xyz_bytes = (fixtures_dir / "unsupported_file.xyz").read_bytes()
    with pytest.raises(ValidationError, match="not supported"):
        default_validator.validate("test.xyz", xyz_bytes)


def test_unsupported_content_type_rejected(default_validator: FileValidator):
    with pytest.raises(ValidationError, match="Content type .* is not supported"):
        default_validator.validate("image.pdf", b"%PDF-1.4...", "image/png")


def test_empty_file_rejected(default_validator: FileValidator, fixtures_dir: Path):
    empty_bytes = (fixtures_dir / "empty.pdf").read_bytes()
    with pytest.raises(ValidationError, match="empty \\(0 bytes\\)"):
        default_validator.validate("empty.pdf", empty_bytes, "application/pdf")


def test_oversized_file_rejected():
    validator = FileValidator(max_file_size_bytes=100)
    oversized = b"A" * 101
    with pytest.raises(ValidationError, match="exceeds maximum allowed size"):
        validator.validate("test.txt", oversized, "text/plain")
