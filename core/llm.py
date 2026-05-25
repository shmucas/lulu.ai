import httpx
from typing import AsyncIterator

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"
MAX_TOKENS = 500


async def stream_response(prompt: str, history: list[dict]) -> AsyncIterator[str]:
    messages = _build_prompt(prompt, history)
    payload = {
        "model": MODEL,
        "prompt": messages,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", OLLAMA_URL, json=payload) as response:
            response.raise_for_status()
            token_count = 0
            async for line in response.aiter_lines():
                if not line:
                    continue
                import json
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    token_count += len(token.split())
                    yield token
                if data.get("done") or token_count >= MAX_TOKENS:
                    break


def _build_prompt(user_message: str, history: list[dict]) -> str:
    parts = []
    for turn in history:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "user":
            parts.append(f"User: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")
    parts.append(f"User: {user_message}")
    parts.append("Assistant:")
    return "\n".join(parts)
