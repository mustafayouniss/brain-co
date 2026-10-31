"""Provider-Agnostic LLM Protocol for General Brain.

General Brain defines this completion interface for engines that utilize
interpretive intelligence. General Brain does NOT import any vendor SDKs,
third-party AI libraries, or hardcode vendor models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Protocol, runtime_checkable


class LLMRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class LLMMessage:
    role: LLMRole
    content: str


@dataclass(frozen=True)
class LLMRequest:
    """Provider-independent LLM request envelope. Zero vendor-specific model assumptions."""

    messages: tuple[LLMMessage, ...]
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    model_hint: Optional[str] = None  # Generic hint (e.g. 'fast', 'reasoning'); adapter maps to concrete model
    timeout_seconds: float = 30.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    """Normalized response envelope."""

    content: str
    model_identifier: Optional[str] = None
    finish_reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMClientError(Exception):
    """Normalized provider-agnostic failure."""

    def __init__(
        self,
        message: str,
        is_retryable: bool = False,
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.is_retryable = is_retryable
        self.detail = detail or {}


@runtime_checkable
class ILLMClient(Protocol):
    """Abstract completion protocol owned strictly by General Brain."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Asynchronously execute completion."""
        ...
