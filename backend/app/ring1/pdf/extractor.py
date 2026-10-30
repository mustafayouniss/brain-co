"""Real PDF text and metadata extractor for Ring 1 using pypdf.

Complies strictly with Ring 1 PDF ingestion specifications:
- Pure Python in-memory stream processing (no external C binaries or shell tools)
- Validates file signatures (%PDF-) and size limits
- Extracts page-by-page text preserving 1-indexed page provenance
- Detects encryption/password protection and malformed structures cleanly
- Detects scanned documents (empty/minimal text) and marks OCR required
- Generates safe server-side identifiers with SHA-256 fingerprint
- Measures extraction duration and character counts accurately
"""

from __future__ import annotations

import hashlib
import io
import logging
import time
from typing import Any

import pypdf
from pypdf.errors import EmptyFileError, PdfReadError

from app.ring1.pdf.schemas import PDFExtractionResult, PDFPageContent

logger = logging.getLogger("ring1.pdf.extractor")

DEFAULT_MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
PDF_MAGIC_HEADER = b"%PDF-"


class PDFExtractionError(Exception):
    """Base exception for PDF extraction failures."""


class MalformedPDFError(PDFExtractionError):
    """Raised when the uploaded file is not a valid PDF."""


class EncryptedPDFError(PDFExtractionError):
    """Raised when the PDF is password-protected or encrypted."""


class OversizedPDFError(PDFExtractionError):
    """Raised when the PDF exceeds the maximum allowed file size."""


class EmptyPDFError(PDFExtractionError):
    """Raised when the uploaded file is 0 bytes."""


class PDFExtractor:
    """Production-grade, secure PDF extractor for Ring 1."""

    def __init__(self, max_size_bytes: int = DEFAULT_MAX_PDF_SIZE_BYTES) -> None:
        self.max_size_bytes = max_size_bytes

    def extract(
        self,
        content: bytes,
        original_filename: str = "document.pdf",
        filename: str | None = None,
    ) -> PDFExtractionResult:
        """Alias for extract_from_bytes."""
        name = filename or original_filename
        return self.extract_from_bytes(content, original_filename=name)

    def extract_from_bytes(
        self,
        content: bytes,
        original_filename: str = "document.pdf",
    ) -> PDFExtractionResult:
        """Extract text and metadata from raw PDF bytes page by page.

        Validates magic header, parses structure with pypdf, and captures page provenance.
        """
        t0 = time.perf_counter()

        # 1. Size and Empty Validation
        if not content or len(content) == 0:
            raise EmptyPDFError("Uploaded PDF is empty (0 bytes).")

        size_bytes = len(content)
        if size_bytes > self.max_size_bytes:
            raise OversizedPDFError(
                f"PDF size ({size_bytes} bytes) exceeds maximum limit ({self.max_size_bytes} bytes)."
            )

        # 2. Magic Header Signature Validation
        if not content.startswith(PDF_MAGIC_HEADER):
            # Check first 1024 bytes in case of leading whitespace or BOM
            header_offset = content[:1024].find(PDF_MAGIC_HEADER)
            if header_offset == -1:
                raise MalformedPDFError(
                    "Invalid file signature: file does not start with standard PDF magic bytes (%PDF-)."
                )

        # 3. SHA-256 Fingerprint
        checksum_sha256 = hashlib.sha256(content).hexdigest()

        # 4. In-Memory Parsing via pypdf
        stream = io.BytesIO(content)
        try:
            reader = pypdf.PdfReader(stream)
        except (PdfReadError, EmptyFileError) as exc:
            raise MalformedPDFError(f"Failed to parse PDF document structure: {str(exc)}") from exc
        except Exception as exc:
            raise MalformedPDFError(f"Unexpected error reading PDF structure: {str(exc)}") from exc

        # 5. Encryption / Password Check
        if reader.is_encrypted:
            # Try decrypting with empty password (some standard PDFs are marked encrypted without password)
            try:
                decrypt_success = reader.decrypt("")
                if decrypt_success == 0:
                    raise EncryptedPDFError("The PDF document is password-protected and cannot be decrypted.")
            except Exception as exc:
                raise EncryptedPDFError(
                    f"The PDF document is password-protected or encrypted: {str(exc)}"
                ) from exc

        # 6. Metadata Extraction
        doc_metadata: dict[str, Any] = {}
        try:
            raw_meta = reader.metadata
            if raw_meta:
                for k, v in raw_meta.items():
                    clean_k = str(k).lstrip("/").lower()
                    doc_metadata[clean_k] = str(v) if v is not None else ""
        except Exception as exc:
            logger.warning("Could not parse PDF metadata: %s", exc)

        page_count = len(reader.pages)
        if page_count == 0:
            raise MalformedPDFError("PDF has 0 pages.")

        # 7. Page-by-Page Text Extraction with Provenance
        pages: list[PDFPageContent] = []
        total_chars = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception as exc:
                logger.warning("Error extracting text from page %d: %s", page_idx, exc)
                page_text = ""

            cleaned_text = page_text.strip()
            char_count = len(cleaned_text)
            word_count = len(cleaned_text.split()) if cleaned_text else 0
            is_blank = char_count == 0

            total_chars += char_count
            pages.append(
                PDFPageContent(
                    page_number=page_idx,
                    text=cleaned_text,
                    char_count=char_count,
                    word_count=word_count,
                    is_blank=is_blank,
                )
            )

        # 8. Scanned Document Detection
        # If total characters across pages is under 20 (and page count >= 1), text extraction
        # is insufficient and OCR is required.
        is_scanned = total_chars < 20
        requires_ocr = is_scanned

        duration_ms = round((time.perf_counter() - t0) * 1000, 2)

        return PDFExtractionResult(
            original_filename=original_filename,
            file_size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            page_count=page_count,
            total_characters=total_chars,
            pages=pages,
            is_scanned=is_scanned,
            requires_ocr=requires_ocr,
            metadata=doc_metadata,
            duration_ms=duration_ms,
        )
