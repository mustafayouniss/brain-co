from typing import Optional
import httpx

from ai.providers.base_openai import BaseOpenAICompatibleProvider


class KimiProvider(BaseOpenAICompatibleProvider):
    """Kimi / Moonshot AI provider (moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k, kimi-k1.5)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "moonshot-v1-8k",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 90.0,
    ):
        super().__init__(
            provider_id="kimi",
            api_key=api_key,
            base_url=base_url or "https://api.moonshot.cn/v1",
            default_model=default_model,
            timeout=timeout,
            client=client,
            requires_api_key=True,
        )
