import os
import json
import re
from rapidfuzz import fuzz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "..", "data", "products.json")

STOPWORDS = {
    "apa", "itu", "fungsi", "harga", "manfaat",
    "untuk", "berapa", "produk", "cni", "apakah", "dan"
}

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)  # hapus ? ! .
    words = [w for w in text.split() if w not in STOPWORDS]
    return " ".join(words)

def search_products(query: str, products: list, limit: int = 3):
    q = normalize(query)
    scored = []

    for p in products:
        corpus = " ".join([
            p.get("nama", ""),
            p.get("kode", ""),
            p.get("deskripsi", ""),
            p.get("fungsi", "")
        ]).lower()

        score = fuzz.token_set_ratio(q, corpus)

        if score >= 50:
            scored.append((score, p))

    # sort berdasarkan skor
    scored.sort(key=lambda x: x[0], reverse=True)

    # fallback: jika kosong → ambil produk teratas
    #if not scored and products:
    #    return products[:1]

    return [p for _, p in scored[:limit]]


def load_products() -> list:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
