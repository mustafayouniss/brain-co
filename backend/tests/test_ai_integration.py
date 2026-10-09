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
