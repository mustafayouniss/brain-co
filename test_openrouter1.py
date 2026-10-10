
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY is missing from .env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

MODEL = "openrouter/auto"


def ask(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=200,
    )

    message = response.choices[0].message

    print("\nModel used:", response.model)
    print("Response:", message.content)

    return message.content


if __name__ == "__main__":
    conversation = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI assistant. "
                "Answer clearly and concisely. "
                "Do not reveal internal reasoning."
            ),
        },
        {
            "role": "user",
            "content": "Explain RAG in exactly two simple sentences.",
        },
    ]

    print("TEST 1: First question")
    first_answer = ask(conversation)

    conversation.append({
        "role": "assistant",
        "content": first_answer or "",
    })

    conversation.append({
        "role": "user",
        "content": "Give me one practical example of RAG.",
    })

    print("\nTEST 2: Follow-up question")
    ask(conversation)

    print("\nTEST COMPLETED")