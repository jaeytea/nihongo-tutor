import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def ask_llm(system_prompt: str, user_message: str) -> str | None:
    try:
        # Keep shell variables authoritative while loading this project's .env.
        load_dotenv(Path(__file__).resolve().with_name(".env"))
        client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL") or "http://localhost:11434/v1",
            api_key=os.getenv("LLM_API_KEY") or "ollama",
            timeout=20.0,
        )
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL") or "gemma3:4b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content
    except Exception:
        return None