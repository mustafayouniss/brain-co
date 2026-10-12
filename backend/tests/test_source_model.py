"""
Database tests for the Source SQLAlchemy model and source_service.
Enforces that Source Memory records are persisted with full integrity in PostgreSQL.
"""
from datetime import datetime
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.source import Source
from app.models.user import User
from app.services.source_service import create_source


@pytest.fixture
def test_user(db_session) -> User:
    """Create a persistent user record for foreign key testing."""
    user = User(
        email=f"uploader_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Uploader Lawyer",
        hashed_password="not-a-real-hash",
        role="employee",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_source_success(db_session, test_user: User):
    """Source is persisted with generated UUID, valid foreign key, timestamps, and metadata."""
    sha = "a" * 64
    source = Source(
        original_filename="Civil_Code_Egyptian.pdf",
        content_type="application/pdf",
        size_bytes=2048,
        checksum_sha256=sha,
        storage_key="sources/fake-id/Civil_Code_Egyptian.pdf",
        uploaded_by=test_user.id,
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    assert isinstance(source.id, uuid.UUID)
    assert isinstance(source.created_at, datetime)
    assert isinstance(source.updated_at, datetime)
    assert source.original_filename == "Civil_Code_Egyptian.pdf"
    assert source.content_type == "application/pdf"
    assert source.size_bytes == 2048
    assert source.checksum_sha256 == sha
    assert source.source_type == "document"
    assert source.storage_mode == "local"
    assert source.storage_key == "sources/fake-id/Civil_Code_Egyptian.pdf"
    assert source.status == "ingested"
    assert source.uploaded_by == test_user.id


def test_source_explicit_stable_uuid(db_session, test_user: User):
    """Source accepts an explicit stable UUID generated at pipeline ingestion."""
    explicit_id = uuid.uuid4()
    source = Source(
        id=explicit_id,
        original_filename="Statement.txt",
        content_type="text/plain",
        size_bytes=512,
        checksum_sha256="b" * 64,
        storage_key=f"sources/{explicit_id}/Statement.txt",
        uploaded_by=test_user.id,
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    assert source.id == explicit_id


def test_source_size_bytes_positive_constraint(db_session, test_user: User):
    """Check constraint ck_sources_size_bytes_positive rejects size_bytes <= 0."""
    source = Source(
        original_filename="empty.pdf",
        content_type="application/pdf",
        size_bytes=0,  # Violates size_bytes > 0
        checksum_sha256="c" * 64,
        storage_key="sources/bad/empty.pdf",
        uploaded_by=test_user.id,
    )
    db_session.add(source)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_source_foreign_key_enforced(db_session):
    """Foreign key constraint rejects uploads with non-existent user IDs."""
    non_existent_user = uuid.uuid4()
    source = Source(
        original_filename="doc.pdf",
        content_type="application/pdf",
        size_bytes=100,
        checksum_sha256="d" * 64,
        storage_key="sources/bad/doc.pdf",
        uploaded_by=non_existent_user,
    )
    db_session.add(source)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_source_service_create_source(db_session, test_user: User):
    """create_source flushes but lets caller control transaction commit."""
    explicit_id = uuid.uuid4()
    source = create_source(
        db_session,
        source_id=explicit_id,
        original_filename="Service_Test.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        checksum_sha256="e" * 64,
        storage_key=f"sources/{explicit_id}/Service_Test.pdf",
        uploaded_by=test_user.id,
    )

    # Flushed into session
    assert source.id == explicit_id
    # Caller commits
    db_session.commit()
    db_session.refresh(source)
    assert source.id == explicit_id
