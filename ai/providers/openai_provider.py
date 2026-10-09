from typing import Optional
import httpx

from ai.providers.base_openai import BaseOpenAICompatibleProvider


class OpenAIProvider(BaseOpenAICompatibleProvider):
    """OpenAI implementation (GPT-4o, GPT-4, GPT-3.5, O1/O3)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4o",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 60.0,
    ):
        super().__init__(
            provider_id="openai",
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            default_model=default_model,
            timeout=timeout,
            client=client,
            requires_api_key=True,
        )
