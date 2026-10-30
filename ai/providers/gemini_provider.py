from typing import Optional
import httpx

from ai.providers.base_openai import BaseOpenAICompatibleProvider


class GeminiProvider(BaseOpenAICompatibleProvider):
    """Google Gemini implementation via OpenAI-compatible endpoint."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gemini-3.5-flash-lite",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 60.0,
    ):
        super().__init__(
            provider_id="gemini",
            api_key=api_key,
            base_url=base_url or "https://generativelanguage.googleapis.com/v1beta/openai",
            default_model=default_model,
            timeout=timeout,
            client=client,
            requires_api_key=True,
        )
