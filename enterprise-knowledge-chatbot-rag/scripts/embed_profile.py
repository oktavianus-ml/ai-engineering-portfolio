import json
import requests
import faiss
import numpy as np
from pathlib import Path

from config import (
    PROFILE_VECTOR_DIR,
    OLLAMA_EMBED_URL,
    EMBED_MODEL,
)

# =========================
# SOURCE PROFILE DATA
# =========================
PROFILE_SOURCE_FILE = Path("data/processed/profile.json")
# Pastikan file ini ADA dan berisi data profile perusahaan

# =========================
# EMBEDDING FUNCTION
# =========================
def embed_text(text: str) -> np.ndarray:
    """
    Embed teks menggunakan Ollama embedding model.
    HARUS sama dengan model yang dipakai di retriever.
    """
    r = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": EMBED_MODEL,
            "prompt": text,
        },
        timeout=60,
    )
    r.raise_for_status()

    return np.array(r.json()["embedding"], dtype="float32")


# =========================
# BUILD PROFILE VECTORSTORE
# =========================
def build_profile_index():
    if not PROFILE_SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Profile source file tidak ditemukan: {PROFILE_SOURCE_FILE}"
        )

    with open(PROFILE_SOURCE_FILE, encoding="utf-8") as f:
        profiles = json.load(f)

    vectors = []
    metadata = []

    for item in profiles:
        text = item.get("text", "").strip()
        if not text:
            continue

        vec = embed_text(text)
        vectors.append(vec)
        metadata.append(item)

    if not vectors:
        raise ValueError("Tidak ada data profile untuk di-embed.")

    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.vstack(vectors))

    PROFILE_VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(PROFILE_VECTOR_DIR / "index.faiss"))
    with open(PROFILE_VECTOR_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("✅ Profile vectorstore berhasil dibuat.")
    print(f"   - Total chunk : {len(metadata)}")
    print(f"   - Dimensi     : {dim}")
    print(f"   - Lokasi      : {PROFILE_VECTOR_DIR}")


if __name__ == "__main__":
    build_profile_index()
