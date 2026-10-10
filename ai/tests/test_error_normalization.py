from ai.core.types.error import LLMError, LLMErrorType


def test_should_create_error_with_type_and_message():
    err = LLMError(
        error_type=LLMErrorType.INVALID_REQUEST,
        message="Invalid max_tokens value",
    )
    assert err.error_type == LLMErrorType.INVALID_REQUEST
    assert err.message == "Invalid max_tokens value"
    assert err.provider_id is None
    assert err.original_error is None
    assert "INVALID_REQUEST: Invalid max_tokens value" in str(err)


def test_should_accept_optional_provider_parameter():
    err = LLMError(
        error_type=LLMErrorType.AUTHENTICATION_FAILED,
        message="API key expired",
        provider_id="deepseek",
    )
    assert err.provider_id == "deepseek"
    assert "AUTHENTICATION_FAILED [deepseek]: API key expired" in str(err)


def test_should_accept_optional_original_error_parameter():
    original = ValueError("Underlying value issue")
    err = LLMError(
        error_type=LLMErrorType.UNKNOWN,
        message="Wrapped failure",
        provider_id="kimi",
        original_error=original,
    )
    assert err.original_error is original


def test_should_have_all_required_error_types():
    expected_types = {
        "AUTHENTICATION_FAILED",
        "RATE_LIMITED",
        "MODEL_UNAVAILABLE",
        "INVALID_REQUEST",
        "TIMEOUT",
        "PROVIDER_ERROR",
        "UNKNOWN",
    }
    actual_types = {t.value for t in LLMErrorType}
    assert expected_types.issubset(actual_types)
