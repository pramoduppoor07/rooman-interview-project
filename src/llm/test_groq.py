"""Quick smoke test for the Groq client."""
from dotenv import load_dotenv
load_dotenv()

from src.llm.groq_client import chat_json

result = chat_json(
    system_prompt='You respond only with valid JSON.',
    user_message='Return {"status": "ok", "model": "working"}',
)
print(result)
assert result.get("status") == "ok", f"Unexpected response: {result}"
print("Groq client OK")
