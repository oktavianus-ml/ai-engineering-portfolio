# api/embedding.py
import requests
from config import OLLAMA_EMBED_URL, EMBED_MODEL


def embed_text(text: str) -> list[float]:
    """
    Generate embedding vector using Ollama HTTP API.
    Single source of truth for embedding.
    """

    payload = {
        "model": EMBED_MODEL,
        "prompt": text
    }

    response = requests.post(OLLAMA_EMBED_URL, json=payload)
    response.raise_for_status()

    data = response.json()
    return data["embedding"]
