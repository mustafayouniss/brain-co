from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class TokenUsage(BaseModel):
    """Token consumption metrics for request execution."""

    model_config = ConfigDict(frozen=True)

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


LLMFinishReason = Literal["stop", "length", "content_filter", "tool_calls", "unknown"]


class LLMResponse(BaseModel):
    """Normalized response generated from an LLM provider."""

    model_config = ConfigDict(extra="ignore")

    content: str
    model: str
    finish_reason: LLMFinishReason = "stop"
    usage: Optional[TokenUsage] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
