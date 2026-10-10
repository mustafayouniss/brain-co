
from typing import Optional
import httpx

from ai.providers.base_openai import BaseOpenAICompatibleProvider


class HuggingFaceProvider(BaseOpenAICompatibleProvider):
    """Hugging Face implementation (OpenAI-compatible Inference Providers)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "deepseek-ai/DeepSeek-V4.1-Flash",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 60.0,
    ):
        super().__init__(
            provider_id="huggingface",
            api_key=api_key,
            base_url=base_url or "https://router.huggingface.co/v1",
            default_model=default_model,
            timeout=timeout,
            client=client,
            requires_api_key=True,
        )