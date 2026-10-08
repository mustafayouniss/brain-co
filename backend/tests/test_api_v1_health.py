from unittest.mock import MagicMock

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_db
from app.core.config import settings
from app.main import app


def test_health_db_success(client):
    """GET /api/v1/health/db returns 200 and healthy status when database is reachable."""
    response = client.get("/api/v1/health/db")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "database": "up"}


def test_health_db_failure_returns_503_without_leaks(client):
    """GET /api/v1/health/db returns 503 on database failure without leaking credentials."""
    canary_secret = "SECRET_CANARY_123"

    mock_db = MagicMock()
    mock_db.execute.side_effect = SQLAlchemyError(f"Connection error: {canary_secret}")

    def _broken_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _broken_get_db
    try:
        response = client.get("/api/v1/health/db")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {
        "error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "Database is unreachable",
        }
    }
    assert canary_secret not in response.text
    assert settings.POSTGRES_PASSWORD not in response.text
