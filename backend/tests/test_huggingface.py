
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

async def main():
    api_key = (
        os.getenv("HUGGINGFACE_API_KEY")
        or os.getenv("HF_TOKEN")
    )

    if not api_key:
        print("ERROR: HUGGINGFACE_API_KEY or HF_TOKEN was not found.")
        return

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv(
            "HUGGINGFACE_BASE_URL",
            "https://router.huggingface.co/v1",
        ),
    )

    try:
        response = await client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            messages=[
                {
                    "role": "user",
                    "content": "Reply with: Hugging Face connection successful!",
                }
            ],
            max_tokens=60,
        )

        print("Provider: Hugging Face")
        print("Model:", response.model)
        print("Response:", response.choices[0].message.content)

    except Exception as exc:
        print("Error type:", type(exc).__name__)
        print("Error:", str(exc))

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())