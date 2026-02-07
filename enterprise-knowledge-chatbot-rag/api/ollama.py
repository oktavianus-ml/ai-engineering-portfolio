import os
import requests

# =========================
# CONFIG
# =========================
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

MODEL = os.getenv("MODEL", "gemma3:4b")

# =========================
# MAIN FUNCTION
# =========================
def ask_ollama(question: str, products: list, user_id=None) -> str:

    # =========================
    # BUILD CONTEXT
    # =========================
    context = ""
    for p in products:
        context += f"""
Nama: {p.get('nama', '-')}
Kode: {p.get('kode', '-')}
Harga: Rp {p.get('harga', '-')}
Fungsi: {p.get('fungsi', '-')}
Deskripsi: {p.get('deskripsi', '-')}
"""

    prompt = f"""
Anda adalah asisten produk CNI Indonesia.

ATURAN WAJIB:
- Jawab HANYA dalam Bahasa Indonesia
- Jawaban harus singkat, jelas, dan informatif
- Jika ditanya harga, sebutkan langsung
- Jangan menambahkan disclaimer atau asumsi

DATA PRODUK:
{context}

PERTANYAAN:
{question}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "temperature": 0.3,
        "stream": False
    }

    # =========================
    # CALL OLLAMA
    # =========================
    try:
        r = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=180  # ⬅️ penting untuk VM
        )
        r.raise_for_status()

        answer = r.json().get("response", "").strip()

        if not answer:
            return "AI tidak memberikan jawaban."

        return answer

    except requests.exceptions.ReadTimeout:
        return (
            "⚠️ AI membutuhkan waktu lebih lama dari biasanya. "
            "Silakan coba kembali sebentar lagi."
        )

    except Exception as e:
        print("OLLAMA ERROR:", e)
        return "AI sedang tidak tersedia."


def call_llm(prompt: str) -> str:
    """
    Call Ollama LLM using /api/generate endpoint.
    Safe for RAG textual responses.
    """

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    r = requests.post(
        OLLAMA_URL,   # pastikan ini /api/generate
        json=payload,
        timeout=60
    )
    r.raise_for_status()

    data = r.json()

    # Ollama /api/generate returns "response"
    if "response" not in data:
        raise RuntimeError(f"Unexpected Ollama response: {data}")

    return data["response"]

