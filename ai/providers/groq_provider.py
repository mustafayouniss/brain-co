
from typing import Optional
import httpx

from ai.providers.base_openai import BaseOpenAICompatibleProvider


class GroqProvider(BaseOpenAICompatibleProvider):
    """Groq implementation (Llama and other supported models)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "llama-3.3-70b-versatile",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 60.0,
    ):
        super().__init__(
            provider_id="groq",
            api_key=api_key,
            base_url=base_url or "https://api.groq.com/openai/v1",
            default_model=default_model,
            timeout=timeout,
            client=client,
            requires_api_key=True,
        )