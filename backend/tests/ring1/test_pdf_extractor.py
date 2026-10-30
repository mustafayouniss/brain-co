"""Unit tests for Ring 1 real PDF extractor and structured knowledge extraction."""

from __future__ import annotations

import io
import pytest
import pypdf

from app.ring1.pdf.extractor import (
    EmptyPDFError,
    EncryptedPDFError,
    MalformedPDFError,
    OversizedPDFError,
    PDFExtractor,
)
from app.ring1.pdf.structured import StructuredKnowledgeExtractor


from reportlab.pdfgen import canvas


def _create_sample_pdf(pages_text: list[str], password: str | None = None) -> bytes:
    """Helper to create empty pages for scanned document simulation."""
    writer = pypdf.PdfWriter()
    for _ in pages_text:
        writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    if password:
        writer.encrypt(password)
    writer.write(buf)
    return buf.getvalue()


def _create_pdf_with_text(pages_text: list[str], password: str | None = None) -> bytes:
    """Helper to programmatically generate real PDF bytes with extractable text using reportlab."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for text in pages_text:
        c.drawString(72, 750, text)
        c.showPage()
    c.save()

    raw_pdf = buf.getvalue()
    if password:
        reader = pypdf.PdfReader(io.BytesIO(raw_pdf))
        writer = pypdf.PdfWriter()
        writer.append(reader)
        writer.encrypt(password)
        out_buf = io.BytesIO()
        writer.write(out_buf)
        return out_buf.getvalue()

    return raw_pdf


# ---------------------------------------------------------------------------
# 1. Extraction Tests
# ---------------------------------------------------------------------------

def test_extract_valid_multipage_pdf():
    extractor = PDFExtractor()
    page1_text = "Commercial Lease Agreement dated 2026-05-15. Article 147 of Civil Code applies."
    page2_text = "Tenant agrees to pay EGP 45000 monthly. Cairo Court has exclusive jurisdiction."

    pdf_bytes = _create_pdf_with_text([page1_text, page2_text])
    result = extractor.extract_from_bytes(pdf_bytes, original_filename="lease_contract.pdf")

    assert result.original_filename == "lease_contract.pdf"
    assert result.page_count == 2
    assert len(result.pages) == 2
    assert result.is_scanned is False
    assert result.requires_ocr is False
    assert result.total_characters > 50

    # Verify page provenance
    assert result.pages[0].page_number == 1
    assert "Commercial Lease Agreement" in result.pages[0].text
    assert result.pages[1].page_number == 2
    assert "EGP 45000" in result.pages[1].text


def test_extract_empty_pdf_raises():
    extractor = PDFExtractor()
    with pytest.raises(EmptyPDFError):
        extractor.extract_from_bytes(b"", "empty.pdf")


def test_extract_malformed_signature_raises():
    extractor = PDFExtractor()
    with pytest.raises(MalformedPDFError):
        extractor.extract_from_bytes(b"NOT A REAL PDF FILE HEADER", "fake.pdf")


def test_extract_oversized_pdf_raises():
    extractor = PDFExtractor(max_size_bytes=100)
    with pytest.raises(OversizedPDFError):
        extractor.extract_from_bytes(b"%PDF-1.4 " + b"X" * 150, "oversized.pdf")


def test_extract_encrypted_pdf_raises():
    extractor = PDFExtractor()
    pdf_bytes = _create_pdf_with_text(["Confidential content"], password="SecretPassword123")
    with pytest.raises(EncryptedPDFError):
        extractor.extract_from_bytes(pdf_bytes, "protected.pdf")


def test_extract_scanned_pdf_detects_ocr_required():
    extractor = PDFExtractor()
    # Blank pages simulate a scanned document without embedded text
    pdf_bytes = _create_sample_pdf(["", ""])
    result = extractor.extract_from_bytes(pdf_bytes, "scanned_doc.pdf")

    assert result.page_count == 2
    assert result.is_scanned is True
    assert result.requires_ocr is True
    assert result.total_characters == 0


# ---------------------------------------------------------------------------
# 2. Structured Knowledge Extraction Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_structured_knowledge_extraction_with_provenance():
    extractor = PDFExtractor()
    page1 = "Commercial Contract dated 2026-06-01 between Cairo Bank and Delta Corporation."
    page2 = "Pursuant to Article 147 of the Egyptian Civil Code, Tenant must pay EGP 75000 before 2026-07-01."
    pdf_bytes = _create_pdf_with_text([page1, page2])
    result = extractor.extract_from_bytes(pdf_bytes, "contract.pdf")

    knowledge_extractor = StructuredKnowledgeExtractor(llm_service=None)
    knowledge = await knowledge_extractor.extract_knowledge(result)

    assert knowledge.document_id == result.document_id
    assert len(knowledge.facts) > 0
    assert len(knowledge.entities) > 0

    # Verify fact provenance
    page2_facts = [f for f in knowledge.facts if f.page_number == 2]
    assert len(page2_facts) > 0
    assert any("147" in f.statement for f in page2_facts)
    assert any("75000" in f.statement for f in page2_facts)
    assert any("2026-07-01" in f.statement for f in page2_facts)

    # Verify entity provenance
    entities_names = [e.name for e in knowledge.entities]
    assert any("Article 147" in name for name in entities_names)
