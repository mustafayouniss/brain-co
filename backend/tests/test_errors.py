from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import register_exception_handlers


def test_unknown_url_returns_404_in_standard_format(client):
    """Unknown routes return HTTP 404 with standardized error JSON."""
    response = client.get("/api/v1/nonexistent-endpoint-xyz")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Not Found",
        }
    }


def test_method_not_allowed_returns_405_in_standard_format(client):
    """Invoking an invalid HTTP method returns 405 with standardized error JSON."""
    response = client.post("/health")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert response.json() == {
        "error": {
            "code": "METHOD_NOT_ALLOWED",
            "message": "Method Not Allowed",
        }
    }


def test_validation_error_returns_422_in_standard_format():
    """Request validation errors return 422 with sanitized field details on a throwaway app."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    class ItemPayload(BaseModel):
        name: str
        quantity: int

    @test_app.post("/test-validation")
    def create_item(payload: ItemPayload):
        return {"ok": True}

    client = TestClient(test_app, raise_server_exceptions=False)
    # Send invalid type for quantity and missing name
    response = client.post("/test-validation", json={"quantity": "invalid_number"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed"
    details = data["error"]["details"]
    assert isinstance(details, list)
    assert len(details) >= 1

    # Verify each detail has only field, message, type (no input or ctx)
    for item in details:
        assert set(item.keys()) == {"field", "message", "type"}
        assert isinstance(item["field"], str)
        assert isinstance(item["message"], str)
        assert isinstance(item["type"], str)


def test_unhandled_exception_returns_500_generic_message():
    """Unhandled server errors return generic 500 without leaking error details on a throwaway app."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/test-crash")
    def crash_route():
        raise RuntimeError("Internal crash with sensitive detail: SECRET_LEAK_999")

    client = TestClient(test_app, raise_server_exceptions=False)
    response = client.get("/test-crash")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error",
        }
    }
    assert "SECRET_LEAK_999" not in response.text


def test_http_exception_with_non_string_detail_and_headers():
    """HTTPException with non-string detail preserves headers and includes details payload."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/test-custom-http-error")
    def custom_error_route():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"reason": "bad_parameters", "step": 1},
            headers={"X-Custom-Header": "OrgBrainTest"},
        )

    client = TestClient(test_app, raise_server_exceptions=False)
    response = client.get("/test-custom-http-error")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.headers.get("x-custom-header") == "OrgBrainTest"
    assert response.json() == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "An HTTP error occurred",
            "details": {"reason": "bad_parameters", "step": 1},
        }
    }


def test_http_exception_fallback_code_for_unmapped_status():
    """HTTPException with an unmapped status code falls back to HTTP_<status>."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/test-unmapped-status")
    def unmapped_route():
        raise HTTPException(status_code=418, detail="I'm a teapot")

    client = TestClient(test_app, raise_server_exceptions=False)
    response = client.get("/test-unmapped-status")

    assert response.status_code == 418
    assert response.json() == {
        "error": {
            "code": "HTTP_418",
            "message": "I'm a teapot",
        }
    }
