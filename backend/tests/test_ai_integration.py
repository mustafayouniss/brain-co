import pytest
from fastapi import APIRouter, Depends, FastAPI
from starlette.testclient import TestClient

from ai.core.interfaces.provider import ILLMProvider
from ai.core.services.llm_service import LLMService
from ai.core.types.error import LLMError, LLMErrorType
from ai.core.types.request import LLMMessage, LLMRequest
from ai.providers.fake_provider import FakeLLMProvider
from app.api.deps import get_llm_service
from app.core.errors import register_exception_handlers


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI instance with exception handlers and a test AI route."""
    app = FastAPI(title="Test OrgBrain App")
    register_exception_handlers(app)

    router = APIRouter()

    @router.post("/test-ai/ask")
    async def ask_ai(
        prompt: str,
        llm: LLMService = Depends(get_llm_service),
    ):
        request = LLMRequest(
            messages=[LLMMessage(role="user", content=prompt)],
            model="test-model",
        )
        response = await llm.generate(request)
        return {
            "answer": response.content,
            "model": response.model,
            "tokens": response.usage.total_tokens if response.usage else 0,
        }

    @router.get("/test-ai/simulate-rate-limit")
    async def simulate_rate_limit(
        llm: LLMService = Depends(get_llm_service),
    ):
        raise LLMError(
            error_type=LLMErrorType.RATE_LIMITED,
            message="DeepSeek token rate limit reached",
            provider_id="deepseek",
        )

    @router.get("/test-ai/simulate-timeout")
    async def simulate_timeout(
        llm: LLMService = Depends(get_llm_service),
    ):
        raise LLMError(
            error_type=LLMErrorType.TIMEOUT,
            message="Gateway timeout connecting to Kimi API",
            provider_id="kimi",
        )

    app.include_router(router)
    return app


def test_ai_dependency_injection_with_mock_provider(test_app: FastAPI):
    """Verify get_llm_service is injected and dependency override works with FakeLLMProvider."""
    fake_provider = FakeLLMProvider(custom_response="الرد القانوني التجريبي")
    fake_service = LLMService(provider=fake_provider)

    test_app.dependency_overrides[get_llm_service] = lambda: fake_service

    client = TestClient(test_app)
    response = client.post("/test-ai/ask", params={"prompt": "ما حكم عقد البيع؟"})

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "الرد القانوني التجريبي"
    assert data["model"] == "test-model"
    assert len(fake_provider.recorded_requests) == 1
    assert fake_provider.recorded_requests[0].messages[0].content == "ما حكم عقد البيع؟"


def test_ai_rate_limit_maps_to_http_429_envelope(test_app: FastAPI):
    """Verify LLMErrorType.RATE_LIMITED is caught and serialized to HTTP 429."""
    client = TestClient(test_app)
    response = client.get("/test-ai/simulate-rate-limit")

    assert response.status_code == 429
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "AI_RATE_LIMITED"
    assert "DeepSeek token rate limit reached" in data["error"]["message"]
    assert data["error"]["details"]["provider"] == "deepseek"


def test_ai_timeout_maps_to_http_504_envelope(test_app: FastAPI):
    """Verify LLMErrorType.TIMEOUT is caught and serialized to HTTP 504."""
    client = TestClient(test_app)
    response = client.get("/test-ai/simulate-timeout")

    assert response.status_code == 504
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "AI_TIMEOUT"
    assert "Gateway timeout connecting to Kimi API" in data["error"]["message"]
    assert data["error"]["details"]["provider"] == "kimi"


import uuid
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.user import User


@pytest.fixture
def test_user(db_session) -> User:
    user = User(
        email=f"ai_tester_{uuid.uuid4().hex[:8]}@example.com",
        full_name="AI Tester",
        hashed_password=hash_password("validpassword1234"),
        role="employee",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


def test_v1_ai_prompt_anonymous_success_in_dev(client, monkeypatch):
    """Anonymous AI request succeeds when AI_ANONYMOUS_TESTING_ENABLED is True in dev."""
    from app.main import app

    monkeypatch.setattr(settings, "AI_ANONYMOUS_TESTING_ENABLED", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    fake_provider = FakeLLMProvider(custom_response="Anonymous integration verified.")
    fake_service = LLMService(provider=fake_provider)

    app.dependency_overrides[get_llm_service] = lambda: fake_service
    try:
        response = client.post("/api/v1/ai/prompt", json={"prompt": "Hello anonymous"})
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Anonymous integration verified."
        assert "model" in data
        assert "tokens" in data
    finally:
        app.dependency_overrides.pop(get_llm_service, None)


def test_v1_ai_prompt_anonymous_rejected_when_disabled(client, monkeypatch):
    """Anonymous AI request is rejected with 401 when AI_ANONYMOUS_TESTING_ENABLED is False."""
    monkeypatch.setattr(settings, "AI_ANONYMOUS_TESTING_ENABLED", False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    response = client.post("/api/v1/ai/prompt", json={"prompt": "Hello test"})
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers


def test_v1_ai_prompt_anonymous_rejected_in_production(client, monkeypatch):
    """Anonymous AI request is rejected with 401 when ENVIRONMENT is production, even if flag is True."""
    monkeypatch.setattr(settings, "AI_ANONYMOUS_TESTING_ENABLED", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    response = client.post("/api/v1/ai/prompt", json={"prompt": "Hello production"})
    assert response.status_code == 401


def test_settings_refuses_anonymous_in_production():
    """Pydantic model validator refuses initialization when anonymous mode enabled in production."""
    from pydantic import ValidationError
    from app.core.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            SECRET_KEY="test-secret-key-for-test-suite-at-least-32-chars-long",
            ENVIRONMENT="production",
            AI_ANONYMOUS_TESTING_ENABLED=True,
        )
    assert "AI_ANONYMOUS_TESTING_ENABLED cannot be enabled in production environment" in str(exc_info.value)


def test_v1_ai_prompt_authenticated_success(client, auth_headers, monkeypatch):
    """Authenticated AI request succeeds with valid Bearer token even when anonymous mode is disabled."""
    from app.main import app

    monkeypatch.setattr(settings, "AI_ANONYMOUS_TESTING_ENABLED", False)

    fake_provider = FakeLLMProvider(custom_response="Authenticated AI response.")
    fake_service = LLMService(provider=fake_provider)

    app.dependency_overrides[get_llm_service] = lambda: fake_service
    try:
        response = client.post("/api/v1/ai/prompt", json={"prompt": "Hello auth"}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Authenticated AI response."
    finally:
        app.dependency_overrides.pop(get_llm_service, None)


def test_v1_ai_prompt_invalid_token_rejected(client):
    """Invalid or tampered token returns 401."""
    response = client.post(
        "/api/v1/ai/prompt",
        json={"prompt": "Hello"},
        headers={"Authorization": "Bearer invalid.token.value"}
    )
    assert response.status_code == 401


def test_unrelated_endpoints_remain_protected_under_anonymous_ai_mode(client, monkeypatch):
    """Enabling AI_ANONYMOUS_TESTING_ENABLED does not weaken unrelated endpoints (sources, users)."""
    monkeypatch.setattr(settings, "AI_ANONYMOUS_TESTING_ENABLED", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    # Unauthenticated sources request must still return 401
    res = client.post("/api/v1/sources")
    assert res.status_code == 401

    # Unauthenticated user creation must still return 401
    res_user = client.post("/api/v1/users", json={})
    assert res_user.status_code == 401


def test_v1_ai_prompt_endpoint_empty_prompt_rejected(client, auth_headers):
    """Verify POST /api/v1/ai/prompt rejects empty prompt with 422."""
    response = client.post("/api/v1/ai/prompt", json={"prompt": ""}, headers=auth_headers)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_v1_ai_prompt_endpoint_oversized_prompt_rejected(client, auth_headers):
    """Verify POST /api/v1/ai/prompt rejects oversized prompt (>10000 chars) with 422."""
    oversized = "A" * 10001
    response = client.post("/api/v1/ai/prompt", json={"prompt": oversized}, headers=auth_headers)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_v1_ai_prompt_endpoint_provider_error(client, auth_headers):
    """Verify POST /api/v1/ai/prompt handles LLM provider errors with structured envelope."""
    from unittest.mock import AsyncMock
    from app.main import app

    failing_service = LLMService(provider=FakeLLMProvider())
    failing_service.generate = AsyncMock(side_effect=LLMError(
        error_type=LLMErrorType.PROVIDER_ERROR,
        message="Upstream provider unreachable",
        provider_id="mock_provider",
    ))

    app.dependency_overrides[get_llm_service] = lambda: failing_service
    try:
        response = client.post("/api/v1/ai/prompt", json={"prompt": "Hello"}, headers=auth_headers)
        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AI_PROVIDER_ERROR"
        assert "Upstream provider unreachable" in data["error"]["message"]
    finally:
        app.dependency_overrides.pop(get_llm_service, None)
