# Ring 0 AI Infrastructure (Python 3.12)

Provider-agnostic, scalable foundation for AI services in the **Organizational Brain** platform.
Built natively in Python to seamlessly integrate with the FastAPI backend, Data Science pipelines, and higher-level Brain rings (Rings 1 to 10).

---

## 🏛️ Architecture

```text
Higher Brain Rings (Rings 1–10: Brain Core, Knowledge, Legal, Reasoning, WhatsApp, etc.)
       ↓ (depends ONLY on ILLMProvider / LLMService)
┌─────────────────────────────────────────────────────────────┐
│              LLMService (Async, Logging, Metrics)           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────▼──────────────┐
                │   ProviderRegistry (Factory)│
                └──────────────┬──────────────┘
                               │
       ┌───────────────┬───────┴───────┬───────────────┬───────────────┐
       ▼               ▼               ▼               ▼               ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│OpenAIProvider││DeepSeekProvider││OpenRouterProvider││ KimiProvider ││OllamaProvider│
└──────────────┘└──────────────┘└──────────────┘└──────────────┘└──────────────┘
```

---

## 🌟 Key Capabilities & Architectural Invariants

1. **Provider Agnostic & Swappable:** Higher-level code depends only on `ILLMProvider` / `LLMService`. Provider can be changed via `.env` with **zero code changes** across higher-level rings.
2. **Wide Provider Ecosystem:**
   * **OpenAI:** GPT-4o, GPT-4, O1/O3.
   * **DeepSeek:** `deepseek-chat`, `deepseek-reasoner` (R1).
   * **OpenRouter:** Dynamic routing to hundreds of open/closed models (Claude 3.5 Sonnet, Llama 3.3, Qwen).
   * **Kimi (Moonshot AI):** `moonshot-v1-8k`, `moonshot-v1-32k`, `kimi-k1.5`.
   * **Ollama:** Offline / local inference without external API keys.
   * **FakeLLMProvider:** Zero-cost, deterministic mock provider for unit testing & CI.
3. **Async-First Execution:** Uses Python `asyncio` and `httpx.AsyncClient` for high concurrency without blocking the FastAPI event loop.
4. **Normalized Error Handling:** All vendor-specific errors are mapped to `LLMError` with standard `LLMErrorType` categories.
5. **Dynamic Extensibility:** New providers can be registered at runtime via `ProviderRegistry.register("provider_id", CustomProviderClass)`.

---

## 🚀 Quickstart

### 1. Basic Generation with Active Provider from Configuration

```python
import asyncio
from ai.config import ai_config
from ai.core.types import LLMRequest, LLMMessage

async def main():
    # Instantiates LLMService with provider configured in .env (OpenAI, DeepSeek, etc.)
    service = ai_config.create_service()

    request = LLMRequest(
        messages=[
            LLMMessage(role="system", content="You are a legal assistant specializing in Egyptian Civil Law."),
            LLMMessage(role="user", content="Explain the legal principle of Article 147."),
        ],
        model="deepseek-chat", # or use default model
        temperature=0.3,
    )

    response = await service.generate(request)
    print("Answer:", response.content)
    print("Tokens:", response.usage)

asyncio.run(main())
```

### 2. Runtime Provider Swapping

Higher-level rings never need to know the provider implementation details:

```python
from ai.core.services import LLMService
from ai.providers import OpenAIProvider, DeepSeekProvider, KimiProvider

service = LLMService(provider=OpenAIProvider(api_key="..."))
# Later, swap dynamically to DeepSeek or Kimi:
service.set_provider(DeepSeekProvider(api_key="..."))
```

### 3. Using Prompt Templates

```python
from ai.prompts import PromptTemplate

template = PromptTemplate(
    template="Summarize the legal case {{case_number}} for client {{client_name}}.",
    system_prompt="You are an Egyptian Civil Law assistant.",
)

messages = template.to_messages({
    "case_number": "1045/2024",
    "client_name": "Ahmed Mostafa",
})
```

---

## ⚙️ Configuration (.env)

```env
# Active provider: openai, deepseek, openrouter, kimi, ollama, fake
AI_PROVIDER=deepseek
AI_MODEL=deepseek-chat

# Credentials
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...
KIMI_API_KEY=sk-...
```

---

## 🧪 Testing

Run all unit tests with `pytest`:

```bash
python3 -m pytest ai/tests -v
```

All 54 tests run locally with zero cost and no external API keys required.
