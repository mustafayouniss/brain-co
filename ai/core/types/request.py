from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class LLMMessage(BaseModel):
    """Normalized chat message."""

    model_config = ConfigDict(frozen=True)

    role: Literal["system", "user", "assistant"]
    content: str


class LLMRequest(BaseModel):
    """Normalized provider-independent request to an LLM."""

    model_config = ConfigDict(extra="ignore")

    messages: list[LLMMessage]
    model: str
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    stream: bool = False
    extra_headers: Optional[dict[str, str]] = None
    extra_body: Optional[dict[str, Any]] = None
