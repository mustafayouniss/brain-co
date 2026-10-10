
import asyncio
import os

from dotenv import load_dotenv

from ai.providers.registry import ProviderRegistry
from ai.core.types.request import LLMMessage, LLMRequest


load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")


async def main():
    print("=" * 50)
    print("BRAIN-CO OPENROUTER PROVIDER TEST")
    print("=" * 50)

    if not API_KEY:
        print("FAILED: OPENROUTER_API_KEY not found.")
        print("Check the .env file in the project directory.")
        return

    try:
        # Create the provider through the project's registry.
        provider = ProviderRegistry.create(
            "openrouter",
            api_key=API_KEY,
            default_model="openrouter/auto",
            timeout=90.0,
        )

        print("Provider ID:", provider.get_provider_id())
        print("Provider available:", provider.is_available())

        if not provider.is_available():
            print("FAILED: Provider is not configured.")
            return

        # Build a request using the project's LLMRequest interface.
        request = LLMRequest(
            model="openrouter/auto",
            messages=[
                LLMMessage(
                    role="system",
                    content="Answer clearly and concisely.",
                ),
                LLMMessage(
                    role="user",
                    content="What is RAG? Explain in two simple sentences.",
                ),
            ],
            temperature=0.2,
            max_tokens=150,
        )

        print("\nSending request through the project provider...")

        response = await provider.generate(request)

        print("\nTEST PASSED")
        print("Response model:", response.model)
        print("Finish reason:", response.finish_reason)
        print("Response:")
        print(response.content)

        if response.usage:
            print("\nToken usage:", response.usage)

    except Exception as exc:
        print("\nTEST FAILED")
        print("Error type:", type(exc).__name__)
        print("Error:", str(exc))


if __name__ == "__main__":
    asyncio.run(main())