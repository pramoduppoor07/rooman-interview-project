from __future__ import annotations
import os
import json
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY not set")
        _client = Groq(api_key=api_key)
    return _client


def chat_json(system_prompt: str, user_message: str) -> dict:
    """Send a chat completion request and return the parsed JSON response."""
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    raw = response.choices[0].message.content
    return json.loads(raw)
