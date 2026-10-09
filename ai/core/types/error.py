from enum import Enum
from typing import Any, Optional


class LLMErrorType(str, Enum):
    """Standardized error categories across all LLM providers."""

    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    TIMEOUT = "TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    UNKNOWN = "UNKNOWN"


class LLMError(Exception):
    """Normalized exception thrown by LLMService and providers.

    Guarantees higher rings receive structured errors regardless of the underlying LLM provider.
    """

    def __init__(
        self,
        error_type: LLMErrorType,
        message: str,
        provider_id: Optional[str] = None,
        original_error: Optional[Any] = None,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.provider_id = provider_id
        self.original_error = original_error

    def __str__(self) -> str:
        provider_info = f" [{self.provider_id}]" if self.provider_id else ""
        return f"{self.error_type.value}{provider_info}: {self.message}"

    def __repr__(self) -> str:
        return (
            f"LLMError(error_type={self.error_type!r}, "
            f"message={self.message!r}, "
            f"provider_id={self.provider_id!r})"
        )
