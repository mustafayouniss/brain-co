
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables from the project root.
project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")

async def main():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("ERROR: GROQ_API_KEY was not found in the project .env file.")
        return

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv(
            "GROQ_BASE_URL",
            "https://api.groq.com/openai/v1",
        ),
    )

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": "Reply with: Groq connection successful!",
                }
            ],
            max_tokens=50,
        )

        print("Provider: Groq")
        print("Model:", response.model)
        print("Response:", response.choices[0].message.content)

    except Exception as exc:
        print("Groq request failed.")
        print("Error type:", type(exc).__name__)
        print("Error:", str(exc))

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())