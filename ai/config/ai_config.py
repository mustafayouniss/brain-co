import os
from pathlib import Path
from typing import ClassVar, Optional

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

    class _BaseAIConfig(BaseModel):
        pass


class AIConfig(_BaseAIConfig):
    """Configuration and factory for the primary and fallback LLM providers."""

    _DEFAULT_PROVIDER_MODELS: ClassVar[dict[str, str]] = {
        "openai": "gpt-4o",
        "deepseek": "deepseek-chat",
        "openrouter": "deepseek/deepseek-r1",
        "kimi": "moonshot-v1-8k",
        "ollama": "llama3",
        "groq": "openai/gpt-oss-120b",
        "huggingface": "deepseek-ai/DeepSeek-V4.1-Flash",
    }
    _PROVIDER_ALIASES: ClassVar[dict[str, str]] = {
        "moonshot": "kimi",
        "hf": "huggingface",
    }

    # General settings. AI_PROVIDER is the primary provider and AI_MODEL is its
    # optional model override. The ordered fallback list can be changed in .env.
    AI_PROVIDER: str = Field(default_factory=lambda: os.getenv("AI_PROVIDER", "openai"))
    AI_MODEL: str = Field(default_factory=lambda: os.getenv("AI_MODEL", "gpt-4o"))
    AI_FALLBACK_PROVIDERS: str = Field(
        default_factory=lambda: os.getenv(
            "AI_FALLBACK_PROVIDERS",
            "openai,deepseek,openrouter,groq,kimi,huggingface",
        )
    )
    AI_TEMPERATURE: float = Field(
        default_factory=lambda: float(os.getenv("AI_TEMPERATURE", "0.7"))
    )
    AI_MAX_TOKENS: Optional[int] = Field(
        default_factory=lambda: (
            int(os.getenv("AI_MAX_TOKENS")) if os.getenv("AI_MAX_TOKENS") else None
        )
    )

    # Optional provider-specific model overrides used by fallback providers.
    # AI_MODEL remains the selected primary provider's legacy model setting.
    AI_MODEL_OPENAI: Optional[str] = Field(default_factory=lambda: os.getenv("AI_MODEL_OPENAI"))
    AI_MODEL_DEEPSEEK: Optional[str] = Field(default_factory=lambda: os.getenv("AI_MODEL_DEEPSEEK"))
    AI_MODEL_OPENROUTER: Optional[str] = Field(default_factory=lambda: os.getenv("AI_MODEL_OPENROUTER"))
    AI_MODEL_KIMI: Optional[str] = Field(default_factory=lambda: os.getenv("AI_MODEL_KIMI"))
    AI_MODEL_OLLAMA: Optional[str] = Field(default_factory=lambda: os.getenv("AI_MODEL_OLLAMA"))
    AI_MODEL_GROQ: Optional[str] = Field(default_factory=lambda: os.getenv("AI_MODEL_GROQ"))
    AI_MODEL_HUGGINGFACE: Optional[str] = Field(default_factory=lambda: os.getenv("AI_MODEL_HUGGINGFACE"))

    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    OPENAI_BASE_URL: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))

    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY"))
    DEEPSEEK_BASE_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY"))
    OPENROUTER_BASE_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    )

    # Kimi / Moonshot
    KIMI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("KIMI_API_KEY"))
    KIMI_BASE_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    )

    # Ollama. Add it to AI_FALLBACK_PROVIDERS only when the endpoint is reachable
    # from the Backend's runtime network.
    OLLAMA_BASE_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    )

    # Groq
    GROQ_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    GROQ_BASE_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    )

    # Hugging Face
    HUGGINGFACE_API_KEY: Optional[str] = Field(
        default_factory=lambda: os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
    )
    HUGGINGFACE_BASE_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("HUGGINGFACE_BASE_URL", "https://router.huggingface.co/v1")
    )

    @classmethod
    def _canonical_provider_id(cls, provider_id: str) -> str:
        normalized = provider_id.strip().lower()
        return cls._PROVIDER_ALIASES.get(normalized, normalized)

    def _model_for_provider(self, provider_id: str, *, use_primary_model: bool) -> str:
        """Resolve a model for one provider without leaking the primary model to fallbacks."""
        canonical_id = self._canonical_provider_id(provider_id)

        if use_primary_model:
            # Preserve legacy behavior: AI_MODEL configures the primary provider.
            # The historical default 'gpt-4o' should not be sent to a non-OpenAI
            # primary provider when the user has not chosen a provider-specific model.
            if canonical_id == "openai" or self.AI_MODEL != "gpt-4o":
                return self.AI_MODEL

        provider_override = getattr(self, f"AI_MODEL_{canonical_id.upper()}", None)
        return provider_override or self._DEFAULT_PROVIDER_MODELS[canonical_id]

    def create_provider(
        self,
        provider_id: Optional[str] = None,
        *,
        use_primary_model: bool = True,
    ) -> ILLMProvider:
        """Create a registered provider using its own model default unless overridden."""
        from ai.providers.registry import ProviderRegistry

        target_provider = (provider_id or self.AI_PROVIDER).strip().lower()
        canonical_id = self._canonical_provider_id(target_provider)
        if canonical_id == "fake":
            return ProviderRegistry.create("fake")

        if canonical_id not in self._DEFAULT_PROVIDER_MODELS:
            # Preserve support for registry extensions/custom providers.
            return ProviderRegistry.create(target_provider)

        default_model = self._model_for_provider(
            canonical_id,
            use_primary_model=use_primary_model,
        )

        provider_kwargs: dict[str, object]
        if canonical_id == "openai":
            provider_kwargs = {
                "api_key": self.OPENAI_API_KEY,
                "base_url": self.OPENAI_BASE_URL,
                "default_model": default_model,
            }
        elif canonical_id == "deepseek":
            provider_kwargs = {
                "api_key": self.DEEPSEEK_API_KEY,
                "base_url": self.DEEPSEEK_BASE_URL,
                "default_model": default_model,
            }
        elif canonical_id == "openrouter":
            provider_kwargs = {
                "api_key": self.OPENROUTER_API_KEY,
                "base_url": self.OPENROUTER_BASE_URL,
                "default_model": default_model,
            }
        elif canonical_id == "kimi":
            provider_kwargs = {
                "api_key": self.KIMI_API_KEY,
                "base_url": self.KIMI_BASE_URL,
                "default_model": default_model,
            }
        elif canonical_id == "ollama":
            provider_kwargs = {
                "base_url": self.OLLAMA_BASE_URL,
                "default_model": default_model,
            }
        elif canonical_id == "groq":
            provider_kwargs = {
                "api_key": self.GROQ_API_KEY,
                "base_url": self.GROQ_BASE_URL,
                "default_model": default_model,
            }
        elif canonical_id == "huggingface":
            provider_kwargs = {
                "api_key": self.HUGGINGFACE_API_KEY,
                "base_url": self.HUGGINGFACE_BASE_URL,
                "default_model": default_model,
            }
        return ProviderRegistry.create(canonical_id, **provider_kwargs)

    def _fallback_provider_ids(self, primary_provider_id: Optional[str] = None) -> list[str]:
        """Parse fallbacks for the selected primary, preserving order and removing duplicates."""
        fallback_ids: list[str] = []
        seen: set[str] = set()
        primary_id = self._canonical_provider_id(primary_provider_id or self.AI_PROVIDER)

        for raw_provider_id in self.AI_FALLBACK_PROVIDERS.split(","):
            if not raw_provider_id.strip():
                continue
            provider_id = self._canonical_provider_id(raw_provider_id)
            if provider_id == primary_id or provider_id in seen:
                continue
            seen.add(provider_id)
            fallback_ids.append(provider_id)

        return fallback_ids

    def create_service(self, provider_id: Optional[str] = None) -> LLMService:
        """Create an LLM service with primary and ordered fallback providers."""
        primary_id = provider_id or self.AI_PROVIDER
        primary = self.create_provider(primary_id, use_primary_model=True)
        primary_canonical_id = self._canonical_provider_id(primary_id)

        fallback_providers: list[ILLMProvider] = []
        seen = {primary_canonical_id}
        for fallback_id in self._fallback_provider_ids(primary_id):
            canonical_id = self._canonical_provider_id(fallback_id)
            if canonical_id in seen:
                continue
            seen.add(canonical_id)
            fallback_providers.append(
                self.create_provider(canonical_id, use_primary_model=False)
            )

        # The service skips providers without required credentials at request time.
        return LLMService(provider=primary, fallback_providers=fallback_providers)


# Global default configuration instance
ai_config = AIConfig()
