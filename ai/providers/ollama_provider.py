from typing import Optional
import httpx

from ai.providers.base_openai import BaseOpenAICompatibleProvider


class OllamaProvider(BaseOpenAICompatibleProvider):
    """Local Ollama provider for offline/local LLM inference (llama3, mistral, qwen2.5, etc.)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: str = "llama3",
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 120.0,
    ):
        super().__init__(
            provider_id="ollama",
            api_key="ollama",
            base_url=base_url or "http://localhost:11434/v1",
            default_model=default_model,
            timeout=timeout,
            client=client,
            requires_api_key=False,
        )
