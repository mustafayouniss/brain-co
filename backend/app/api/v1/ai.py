"""
AI Endpoint - For demonstration and testing purposes.

This endpoint provides a simple interface to the AI abstraction layer.
Not part of Ring 0 specification - added for end-to-end verification.
"""
from fastapi import APIRouter, Depends
from ai.core.services.llm_service import LLMService
from ai.core.types.request import LLMRequest, LLMMessage
from app.api.deps import get_llm_service
from pydantic import BaseModel

router = APIRouter()


class PromptRequest(BaseModel):
    """Request schema for AI prompt."""
    prompt: str
    model: str = "default"


class PromptResponse(BaseModel):
    """Response schema for AI prompt."""
    content: str
    model: str
    tokens: int


@router.post("/prompt", response_model=PromptResponse)
async def generate_ai_response(
    request: PromptRequest,
    llm: LLMService = Depends(get_llm_service),
):
    """
    Generate an AI response using the configured provider.

    This endpoint uses the LLMService abstraction layer, which supports
    multiple providers (OpenAI, DeepSeek, OpenRouter, Kimi, Ollama, Fake).

    For testing, the Fake provider is recommended as it provides
    deterministic responses without requiring API credentials.
    """
    llm_request = LLMRequest(
        messages=[LLMMessage(role="user", content=request.prompt)],
        model=request.model,
    )
    response = await llm.generate(llm_request)

    return PromptResponse(
        content=response.content,
        model=response.model,
        tokens=response.usage.total_tokens if response.usage else 0,
    )
