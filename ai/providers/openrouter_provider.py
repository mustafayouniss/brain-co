from typing import Optional
import httpx

from ai.providers.base_openai import BaseOpenAICompatibleProvider


class OpenRouterProvider(BaseOpenAICompatibleProvider):
    """OpenRouter provider routing to multiple model ecosystems (DeepSeek, Claude, Llama, Qwen)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "deepseek/deepseek-r1",
        site_url: Optional[str] = None,
        site_name: Optional[str] = "Organizational Brain",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 90.0,
    ):
        custom_headers = {}
        if site_url:
            custom_headers["HTTP-Referer"] = site_url
        if site_name:
            custom_headers["X-Title"] = site_name

        super().__init__(
            provider_id="openrouter",
            api_key=api_key,
            base_url=base_url or "https://openrouter.ai/api/v1",
            default_model=default_model,
            custom_headers=custom_headers,
            timeout=timeout,
            client=client,
            requires_api_key=True,
        )
