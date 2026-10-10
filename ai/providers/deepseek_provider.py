from typing import Optional
import httpx

from ai.providers.base_openai import BaseOpenAICompatibleProvider


class DeepSeekProvider(BaseOpenAICompatibleProvider):
    """DeepSeek LLM provider (deepseek-chat, deepseek-reasoner / R1)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "deepseek-chat",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 90.0,
    ):
        super().__init__(
            provider_id="deepseek",
            api_key=api_key,
            base_url=base_url or "https://api.deepseek.com",
            default_model=default_model,
            timeout=timeout,
            client=client,
            requires_api_key=True,
        )
