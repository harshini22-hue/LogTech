import os
import requests
from requests.exceptions import RequestException

OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

def run_llm(prompt: str, timeout: int = 180) -> str:
    """
    Call Ollama Chat API with streaming disabled.
    """
    url = f"{OLLAMA_API_BASE}/api/chat"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        r = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )

        if r.status_code == 400:
            raise RuntimeError(f"Ollama 400 Bad Request: {r.text}")

        r.raise_for_status()
        data = r.json()

        if "message" not in data or "content" not in data["message"]:
            raise RuntimeError(f"Unexpected Ollama response: {data}")

        return data["message"]["content"]

    except RequestException as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc
if __name__ == "__main__":
    try:
        resp = run_llm("Reply with exactly: OLLAMA_OK", timeout=30)
        print(resp)
    except Exception as e:
        print("LLM test failed:", e)