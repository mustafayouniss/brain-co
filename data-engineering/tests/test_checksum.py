"""
Tests for SHA-256 fingerprinting calculation.
"""
import io
import hashlib
from pathlib import Path

from orgbrain_ingest.ingestion.checksum import calculate_sha256


def test_sha256_known_vector():
    sample = b"Organizational Brain Legal V1"
    expected = hashlib.sha256(sample).hexdigest()
    assert calculate_sha256(sample) == expected
    assert len(calculate_sha256(sample)) == 64


def test_sha256_deterministic():
    content = b"Deterministic legal content verification."
    h1 = calculate_sha256(content)
    h2 = calculate_sha256(content)
    assert h1 == h2


def test_sha256_stream_matches_bytes():
    content = b"Streamed input bytes testing chunks." * 1000
    stream = io.BytesIO(content)
    
    hash_from_bytes = calculate_sha256(content)
    hash_from_stream = calculate_sha256(stream)
    
    assert hash_from_bytes == hash_from_stream
    # Verify stream position was restored
    assert stream.tell() == 0


def test_sha256_fixtures(fixtures_dir: Path):
    valid_pdf = fixtures_dir / "valid_small.pdf"
    content = valid_pdf.read_bytes()
    expected = hashlib.sha256(content).hexdigest()
    assert calculate_sha256(content) == expected
