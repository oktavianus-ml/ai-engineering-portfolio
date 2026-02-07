import os
import requests
from typing import List, Tuple

from api.learning import (
    get_learned_answer,
    save_pending
)

# =========================
# CONFIG
# =========================
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("MODEL", "llama3")

FAIL_KEYWORDS = [
    "❌",
    "tidak ditemukan",
    "belum tersedia",
    "maaf",
]

# =========================
# HELPER
# =========================
def is_failed_ai_answer(answer: str) -> bool:
    a = answer.lower()
    return any(k in a for k in FAIL_KEYWORDS)

# =========================
# MAIN AI FUNCTION
# =========================
def ask_llama(question: str, products: List[dict]) -> str:
    """
    ALUR FINAL:
    1️⃣ Cek hasil pembelajaran admin (learned_answers)
    2️⃣ Jika tidak ada learned & produk kosong → pending
    3️⃣ Jika ada produk → panggil LLaMA
    4️⃣ Jika AI jawab gagal → pending
    """

    # =========================
    # 1️⃣ CHECK LEARNED ANSWER
    # =========================
    learned_answer = get_learned_answer(question)
    if learned_answer:
        return learned_answer

    # =========================
    # 2️⃣ NO PRODUCT FOUND
    # =========================
    if not products:
        save_pending(question, source="no_product")
        return (
            "❌ Informasi belum tersedia di database CNI. "
            "Pertanyaan Anda telah dicatat dan akan segera kami perbarui."
        )

    # =========================
    # 3️⃣ BUILD CONTEXT
    # =========================
    context = ""
    for p in products:
        context += f"""
Nama: {p.get('nama')}
Kode: {p.get('kode')}
Harga: Rp {p.get('harga')}
Fungsi: {p.get('fungsi')}
Deskripsi: {p.get('deskripsi')}
"""

    # =========================
    # 4️⃣ PROMPT
    # =========================
    prompt = f"""
Anda adalah asisten produk resmi CNI Indonesia.

ATURAN WAJIB:
- Gunakan Bahasa Indonesia
- Jangan menyamakan produk beda kategori
- Jangan membuat klaim medis
- Jika data tidak tersedia, jelaskan dengan sopan
- Jawaban harus logis, ringkas, dan informatif

DATA PRODUK:
{context}

PERTANYAAN USER:
{question}
"""

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Anda adalah asisten produk CNI Indonesia. "
                    "Jawab dengan bahasa Indonesia yang profesional, sopan, dan faktual. "
                    "Jika data tidak tersedia, jangan mengarang."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "stream": False
    }

    # =========================
    # 5️⃣ CALL OLLAMA
    # =========================
    try:
        r = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )
        r.raise_for_status()

        answer = r.json()["message"]["content"]

        # =========================
        # 6️⃣ DETECT FAILED AI ANSWER
        # =========================
        if is_failed_ai_answer(answer):
            save_pending(question, source="ai_failed")

        return answer

    except Exception:
        save_pending(question, source="system_error")
        return (
            "⚠️ Maaf, sistem AI sedang mengalami gangguan. "
            "Pertanyaan Anda telah dicatat dan akan kami tindak lanjuti."
        )
