"""
Integration tests for POST /api/v1/sources endpoint.
"""
import io
import uuid
import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.user import User


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create and flush an active test employee user."""
    user = User(
        email=f"source_uploader_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Source Uploader",
        hashed_password=hash_password("validpassword1234"),
        role="employee",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create Authorization headers with valid Bearer token."""
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


def test_sources_endpoint_unauthorized_returns_401(client):
    """Uploading without authentication token is rejected with 401."""
    files = {"file": ("test.txt", io.BytesIO(b"Sample legal text content"), "text/plain")}
    response = client.post("/api/v1/sources", files=files)
    assert response.status_code == 401


def test_sources_endpoint_success_txt(client, auth_headers, test_user):
    """Valid text document upload returns 201 with SourceResponse."""
    file_bytes = b"Egyptian Civil Law Article 1: Provisions of laws govern all matters to which they refer."
    files = {"file": ("civil_code_snippet.txt", io.BytesIO(file_bytes), "text/plain")}

    response = client.post("/api/v1/sources", files=files, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["original_filename"] == "civil_code_snippet.txt"
    assert data["content_type"] == "text/plain"
    assert data["size_bytes"] == len(file_bytes)
    assert "checksum_sha256" in data
    assert data["status"] == "ingested"
    assert data["source_type"] == "document"


def test_sources_endpoint_rejects_empty_file(client, auth_headers):
    """Uploading an empty file is rejected with 400 Bad Request."""
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    response = client.post("/api/v1/sources", files=files, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_sources_endpoint_rejects_unsupported_file(client, auth_headers):
    """Uploading an unsupported file extension (e.g. .exe) is rejected with 400."""
    files = {"file": ("malicious.exe", io.BytesIO(b"binarycontent"), "application/octet-stream")}
    response = client.post("/api/v1/sources", files=files, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
