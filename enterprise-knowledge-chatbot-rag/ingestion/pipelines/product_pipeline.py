from pypdf import PdfReader
import json
import numpy as np
import faiss
import requests
from pathlib import Path

from config import DATA_RAW_PDF_DIR
import knowledge.products.loader as product_loader
from core.embeddings import embed, normalize


# ==================================================
# PATH CONFIG
# ==================================================

PRODUCT_SOURCE_DIR = DATA_RAW_PDF_DIR / "product"
PRODUCT_VECTOR_DIR = Path("data/vectorstore/product")
PRODUCT_VECTOR_DIR.mkdir(parents=True, exist_ok=True)

# ==================================================
# EMBEDDING CONFIG
# ==================================================

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


def embed_text(text: str) -> list:
    r = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    r.raise_for_status()
    return r.json()["embedding"]

# ==================================================
# LOAD PRODUCT PDF
# ==================================================

def load_product_documents():
    docs = []

    for pdf_path in PRODUCT_SOURCE_DIR.glob("*.pdf"):
        reader = PdfReader(pdf_path)
        pages = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.replace("\n", " ").strip())

        if not pages:
            print(f"❌ NO TEXT: {pdf_path.name}")
            continue

        full_text = " ".join(pages)

        product_name = pdf_path.stem.replace("_", " ")

        print(f"✅ Loaded product: {product_name}")
        print(f"   Text length: {len(full_text)}")

        docs.append({
            "product_name": product_name,
            "source_file": pdf_path.name,
            "text": full_text
        })

    return docs

# ==================================================
# PIPELINE RUNNER
# ==================================================

def run():
    all_chunks = []

    docs = load_product_documents()
    if not docs:
        raise RuntimeError("❌ No product documents found")

    for d in docs:
        chunks = product_loader.build_product_chunks(
            full_text=d["text"],
            source_file=d["source_file"],
            product_name=d["product_name"]
        )
        all_chunks.extend(chunks)

    print(f"DEBUG: total product chunks = {len(all_chunks)}")



    # =========================
    # EMBEDDING + COSINE FAISS
    # =========================

    vectors = []

    for c in all_chunks:
        vec = embed(c["text"])      # single source of truth
        vec = normalize(vec)        # REQUIRED for cosine similarity
        vectors.append(vec)

    vectors_np = np.array(vectors, dtype="float32")

    dim = vectors_np.shape[1]

    # 🔴 PENTING: ganti L2 → IP
    index = faiss.IndexFlatIP(dim)  # IP = Inner Product = Cosine

    index.add(vectors_np)




    faiss.write_index(index, str(PRODUCT_VECTOR_DIR / "index.faiss"))

    with open(PRODUCT_VECTOR_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Product index built ({len(all_chunks)} chunks, dim={dim})")


if __name__ == "__main__":
    run()