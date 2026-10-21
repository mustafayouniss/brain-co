import asyncio
from typing import Any
import pytest

from ai.core.services.llm_service import LLMService
from ai.core.types.error import LLMError, LLMErrorType
from ai.core.types.request import LLMMessage, LLMRequest
from ai.providers.fake_provider import FakeLLMProvider
from ai.utils.logger import ILogger


class MockLogger(ILogger):
    """In-memory logger for asserting event dispatches."""

    def __init__(self):
        self.info_events: list[dict[str, Any]] = []
        self.error_events: list[dict[str, Any]] = []
        self.warning_events: list[dict[str, Any]] = []

    def info(self, data: dict[str, Any]) -> None:
        self.info_events.append(data)

    def error(self, data: dict[str, Any]) -> None:
        self.error_events.append(data)

    def warning(self, data: dict[str, Any]) -> None:
        self.warning_events.append(data)


def test_should_successfully_generate_response():
    provider = FakeLLMProvider(custom_response="Generated answer")
    logger = MockLogger()
    service = LLMService(provider=provider, logger=logger)

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Ping")],
        model="test-model",
    )

    response = asyncio.run(service.generate(request))
    assert response.content == "Generated answer"
    assert response.model == "test-model"


def test_should_log_request_started_and_completed_events():
    provider = FakeLLMProvider(custom_response="Response")
    logger = MockLogger()
    service = LLMService(provider=provider, logger=logger)

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Test")],
        model="model-x",
    )

    asyncio.run(service.generate(request))

    started = next((e for e in logger.info_events if e.get("event") == "llm_request_started"), None)
    completed = next((e for e in logger.info_events if e.get("event") == "llm_request_completed"), None)

    assert started is not None
    assert started["provider"] == "fake"
    assert started["model"] == "model-x"
    assert started["messageCount"] == 1
    assert "correlationId" in started

    assert completed is not None
    assert completed["provider"] == "fake"
    assert completed["model"] == "model-x"
    assert completed["correlationId"] == started["correlationId"]
    assert "latency" in completed


def test_should_log_request_failed_event_on_error():
    err = LLMError(LLMErrorType.RATE_LIMITED, "Rate limit hit", "fake")
    provider = FakeLLMProvider(forced_error=err)
    logger = MockLogger()
    service = LLMService(provider=provider, logger=logger)

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Test")],
        model="model-x",
    )

    with pytest.raises(LLMError) as exc_info:
        asyncio.run(service.generate(request))

    assert exc_info.value.error_type == LLMErrorType.RATE_LIMITED

    failed = next((e for e in logger.error_events if e.get("event") == "llm_request_failed"), None)
    assert failed is not None
    assert failed["errorType"] == "RATE_LIMITED"
    assert failed["errorMessage"] == "Rate limit hit"
    assert "correlationId" in failed


def test_should_include_correlation_id_in_logs():
    provider = FakeLLMProvider()
    logger = MockLogger()
    service = LLMService(provider=provider, logger=logger)

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Test")],
        model="model-x",
    )

    asyncio.run(service.generate(request))
    correlation_id = logger.info_events[0]["correlationId"]
    assert correlation_id.startswith("llm_")


def test_get_provider_should_return_current_provider():
    provider = FakeLLMProvider()
    service = LLMService(provider=provider)
    assert service.get_provider() is provider


def test_set_provider_should_replace_provider_and_log_event():
    p1 = FakeLLMProvider()
    p2 = FakeLLMProvider()
    logger = MockLogger()
    service = LLMService(provider=p1, logger=logger)

    service.set_provider(p2)
    assert service.get_provider() is p2

    change_event = next((e for e in logger.info_events if e.get("event") == "llm_provider_changed"), None)
    assert change_event is not None
    assert change_event["newProvider"] == "fake"


class NamedFakeProvider(FakeLLMProvider):
    """Fake provider with a distinct ID so failover order is observable in tests."""

    def __init__(self, provider_id: str, **kwargs: Any):
        super().__init__(**kwargs)
        self._provider_id = provider_id


def test_should_fallback_to_next_provider_after_authentication_failure():
    primary_error = LLMError(
        LLMErrorType.AUTHENTICATION_FAILED,
        "Invalid API key",
        "primary",
    )
    primary = NamedFakeProvider("primary", forced_error=primary_error)
    fallback = NamedFakeProvider("fallback", custom_response="Fallback answer")
    logger = MockLogger()
    service = LLMService(
        provider=primary,
        fallback_providers=[fallback],
        logger=logger,
    )
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Continue my task")],
        model="",
    )

    response = asyncio.run(service.generate(request))

    assert response.content == "Fallback answer"
    assert len(primary.recorded_requests) == 1
    assert len(fallback.recorded_requests) == 1
    assert fallback.recorded_requests[0].messages == request.messages
    assert fallback.recorded_requests[0].model == request.model
    fallback_event = next(
        event for event in logger.warning_events
        if event.get("event") == "llm_fallback_started"
    )
    assert fallback_event["failedProvider"] == "primary"
    assert fallback_event["nextProvider"] == "fallback"
    completed = next(
        event for event in logger.info_events
        if event.get("event") == "llm_request_completed"
    )
    assert completed["provider"] == "fallback"
    assert completed["fallbackUsed"] is True


def test_should_not_fallback_for_invalid_request_error():
    primary_error = LLMError(
        LLMErrorType.INVALID_REQUEST,
        "Request payload is invalid",
        "primary",
    )
    primary = NamedFakeProvider("primary", forced_error=primary_error)
    fallback = NamedFakeProvider("fallback", custom_response="Should not run")
    service = LLMService(provider=primary, fallback_providers=[fallback])
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model="",
    )

    with pytest.raises(LLMError) as exc_info:
        asyncio.run(service.generate(request))

    assert exc_info.value.error_type == LLMErrorType.INVALID_REQUEST
    assert len(fallback.recorded_requests) == 0


def test_should_skip_unavailable_fallback_and_try_next_configured_provider():
    primary = NamedFakeProvider(
        "primary",
        forced_error=LLMError(LLMErrorType.TIMEOUT, "Timed out", "primary"),
    )
    unavailable = NamedFakeProvider("unavailable", available=False)
    fallback = NamedFakeProvider("fallback", custom_response="Recovered")
    service = LLMService(
        provider=primary,
        fallback_providers=[unavailable, fallback],
    )
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model="",
    )

    response = asyncio.run(service.generate(request))

    assert response.content == "Recovered"
    assert len(unavailable.recorded_requests) == 0
    assert len(fallback.recorded_requests) == 1


def test_should_raise_last_provider_error_when_all_providers_fail():
    primary = NamedFakeProvider(
        "primary",
        forced_error=LLMError(LLMErrorType.TIMEOUT, "Primary timed out", "primary"),
    )
    fallback = NamedFakeProvider(
        "fallback",
        forced_error=LLMError(LLMErrorType.PROVIDER_ERROR, "Fallback failed", "fallback"),
    )
    service = LLMService(provider=primary, fallback_providers=[fallback])
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        model="",
    )

    with pytest.raises(LLMError) as exc_info:
        asyncio.run(service.generate(request))

    assert exc_info.value.error_type == LLMErrorType.PROVIDER_ERROR
    assert "Fallback failed" in exc_info.value.message
