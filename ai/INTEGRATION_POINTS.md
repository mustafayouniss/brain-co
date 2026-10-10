# Ring 0 AI Infrastructure — Backend Integration Guide (Python / FastAPI)

This guide documents the native integration of the **AI Engine** with the **Python 3.12 / FastAPI** backend.

---

## 1. Direct Dependency Injection into FastAPI Routes

Because the AI Engine is built in Python, FastAPI endpoints can directly inject and consume `LLMService` without network overhead or microservice serialization:

```python
# In backend/app/api/deps.py
from functools import lru_cache
from ai.config import ai_config
from ai.core.services import LLMService

@lru_cache()
def get_llm_service() -> LLMService:
    """Singleton LLMService instance configured from root .env."""
    return ai_config.create_service()
```

And in route handlers:

```python
# In backend/app/api/v1/assistance.py
from fastapi import APIRouter, Depends
from ai.core.services import LLMService
from ai.core.types import LLMRequest, LLMMessage
from app.api.deps import get_llm_service

router = APIRouter()

@router.post("/query")
async def ask_legal_brain(
    prompt: str,
    llm: LLMService = Depends(get_llm_service),
):
    request = LLMRequest(
        messages=[LLMMessage(role="user", content=prompt)],
        model=ai_config.AI_MODEL,
    )
    response = await llm.generate(request)
    return {"answer": response.content, "usage": response.usage}
```

---

## 2. Dynamic Provider Swapping across Rings

Higher-level rings (Ring 1 Brain Core, Ring 3 Legal Domain, Ring 7 Reasoning) can use any registered provider:

```python
from ai.providers import ProviderRegistry
from ai.core.services import LLMService

# Dynamically instantiate DeepSeek, Kimi, OpenRouter, or Ollama
provider = ProviderRegistry.create("deepseek", api_key="sk-...")
service = LLMService(provider=provider)
```

---

## 3. Registering New Custom Models

If the team wants to add another Chinese LLM (e.g., Zhipu GLM, Qwen, or Baichuan):

```python
from ai.providers.base_openai import BaseOpenAICompatibleProvider
from ai.providers.registry import ProviderRegistry

class ZhipuProvider(BaseOpenAICompatibleProvider):
    def __init__(self, api_key: str):
        super().__init__(
            provider_id="zhipu",
            api_key=api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4",
            default_model="glm-4",
        )

# Register into the global registry
ProviderRegistry.register("zhipu", ZhipuProvider)

# Now it can be created anywhere:
provider = ProviderRegistry.create("zhipu", api_key="...")
```

---

## 4. Zero Changes Required for Higher-Level Rings

Higher rings code only references:
* `ILLMProvider`
* `LLMService`
* `LLMRequest`
* `LLMResponse`

Switching between providers is controlled purely via configuration (`AI_PROVIDER=deepseek` in `.env`), with **zero lines of code changed** in higher-level rings.
