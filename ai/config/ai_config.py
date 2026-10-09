import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from ai.core.interfaces.provider import ILLMProvider
from ai.core.services.llm_service import LLMService

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class _BaseAIConfig(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=ENV_FILE_PATH,
            env_file_encoding="utf-8",
            extra="ignore",
        )
except ImportError:
    class _BaseAIConfig(BaseModel):  # type: ignore
        pass


class AIConfig(_BaseAIConfig):
    """Centralized AI configuration loading from environment variables or .env file."""

    AI_PROVIDER: str = Field(default_factory=lambda: os.getenv("AI_PROVIDER", "openai"))
    AI_MODEL: str = Field(default_factory=lambda: os.getenv("AI_MODEL", "gpt-4o"))
    AI_TEMPERATURE: float = Field(default_factory=lambda: float(os.getenv("AI_TEMPERATURE", "0.7")))
    AI_MAX_TOKENS: Optional[int] = Field(default_factory=lambda: int(os.getenv("AI_MAX_TOKENS")) if os.getenv("AI_MAX_TOKENS") else None)

    # Provider credentials & endpoints
    OPENAI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    OPENAI_BASE_URL: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))

    DEEPSEEK_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY"))
    DEEPSEEK_BASE_URL: Optional[str] = Field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))

    OPENROUTER_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY"))
    OPENROUTER_BASE_URL: Optional[str] = Field(default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))

    KIMI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("KIMI_API_KEY"))
    KIMI_BASE_URL: Optional[str] = Field(default_factory=lambda: os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"))

    OLLAMA_BASE_URL: Optional[str] = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"))

    def create_provider(self, provider_id: Optional[str] = None) -> ILLMProvider:
        """Create and configure the appropriate ILLMProvider instance based on active settings."""
        from ai.providers.registry import ProviderRegistry

        target_provider = (provider_id or self.AI_PROVIDER).strip().lower()

        if target_provider == "openai":
            return ProviderRegistry.create(
                "openai",
                api_key=self.OPENAI_API_KEY,
                base_url=self.OPENAI_BASE_URL,
                default_model=self.AI_MODEL,
            )
        elif target_provider == "deepseek":
            return ProviderRegistry.create(
                "deepseek",
                api_key=self.DEEPSEEK_API_KEY,
                base_url=self.DEEPSEEK_BASE_URL,
                default_model=self.AI_MODEL if self.AI_MODEL != "gpt-4o" else "deepseek-chat",
            )
        elif target_provider == "openrouter":
            return ProviderRegistry.create(
                "openrouter",
                api_key=self.OPENROUTER_API_KEY,
                base_url=self.OPENROUTER_BASE_URL,
                default_model=self.AI_MODEL if self.AI_MODEL != "gpt-4o" else "deepseek/deepseek-r1",
            )
        elif target_provider in ("kimi", "moonshot"):
            return ProviderRegistry.create(
                "kimi",
                api_key=self.KIMI_API_KEY,
                base_url=self.KIMI_BASE_URL,
                default_model=self.AI_MODEL if self.AI_MODEL != "gpt-4o" else "moonshot-v1-8k",
            )
        elif target_provider == "ollama":
            return ProviderRegistry.create(
                "ollama",
                base_url=self.OLLAMA_BASE_URL,
                default_model=self.AI_MODEL if self.AI_MODEL != "gpt-4o" else "llama3",
            )
        elif target_provider == "fake":
            return ProviderRegistry.create("fake")
        else:
            return ProviderRegistry.create(target_provider)

    def create_service(self, provider_id: Optional[str] = None) -> LLMService:
        """Instantiate an LLMService ready to serve requests."""
        provider = self.create_provider(provider_id=provider_id)
        return LLMService(provider=provider)


# Global default configuration instance
ai_config = AIConfig()
