import json
import httpx
from typing import AsyncIterator

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"
MAX_TOKENS = 500


async def stream_response(prompt: str, history: list[dict], context: str = "") -> AsyncIterator[str]:
    messages = _build_messages(prompt, history, context)
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", OLLAMA_URL, json=payload) as response:
            response.raise_for_status()
            token_count = 0
            async for line in response.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                token = data.get("message", {}).get("content", "")
                if token:
                    token_count += len(token.split())
                    yield token
                if data.get("done") or token_count >= MAX_TOKENS:
                    break


def _system_prompt() -> str:
    from datetime import datetime
    now = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    return (
        f"You are Lulu, a friendly and concise voice assistant. "
        f"Always refer to yourself as Lulu, never as 'AI' or 'assistant'. "
        f"Keep responses short and conversational. "
        f"The current date and time is {now}. "
        f"When live data is provided, answer using ONLY that data — do not add anything from memory or training."
    )


def _build_messages(user_message: str, history: list[dict], context: str = "") -> list[dict]:
    messages = [{"role": "system", "content": _system_prompt()}]

    for turn in history:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})

    content = user_message
    if context:
        content = f"{user_message}\n\n[Live data for this query — use only this, nothing from memory]:\n{context}"

    messages.append({"role": "user", "content": content})
    return messages
