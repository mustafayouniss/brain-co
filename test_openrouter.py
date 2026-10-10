
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY is missing from .env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

try:
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "user",
                "content": "Explain what RAG is in two simple sentences."
            }
        ],
        max_tokens=100,
    )

    print("Connection successful!")
    print("Model used:", response.model)
    print("Response:", response.choices[0].message.content)

except Exception as exc:
    print("Request failed:", type(exc).__name__, str(exc))

finally:
    client.close()