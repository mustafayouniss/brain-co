
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

project_root = Path(__file__).resolve().parent
load_dotenv(project_root / ".env")

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError("DEEPSEEK_API_KEY was not found in .env")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": "Explain RAG in two simple sentences."
            }
        ],
        max_tokens=100,
    )

    print("DeepSeek connection successful!")
    print("Model:", response.model)
    print("Response:", response.choices[0].message.content)

except Exception as exc:
    print("Request failed:", type(exc).__name__, str(exc))

finally:
    client.close()