# ingestion/pipelines/profile_pipeline.py

from pypdf import PdfReader
import json
import numpy as np
import faiss
import requests
from pathlib import Path

from config import DATA_RAW_PDF_DIR
import knowledge.profile.loader as profile_loader

# ==================================================
# PATH CONFIG
# ==================================================

PROFILE_SOURCE_DIR = DATA_RAW_PDF_DIR / "company sop profile"
PROFILE_VECTOR_DIR = Path("data/vectorstore/profile")
PROFILE_VECTOR_DIR.mkdir(parents=True, exist_ok=True)

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
# STEP 1 — LOAD PROFILE PDF (ROBUST)
# ==================================================

def load_profile_documents():
    docs = []

    for pdf_path in PROFILE_SOURCE_DIR.glob("*.pdf"):
        if "profile" not in pdf_path.name.lower():
            continue
        reader = PdfReader(pdf_path)   # ✅ PASTI TER-DEFINE
        pages = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.replace("\n", " ").strip())

        if not pages:
            print(f"❌ NO TEXT EXTRACTED: {pdf_path.name}")
            continue

        full_text = " ".join(pages)

        print(f"✅ Loaded profile: {pdf_path.name}")
        print(f"   Text length: {len(full_text)}")

        docs.append({
            "source_file": pdf_path.name,
            "text": full_text
        })

    return docs

# ==================================================
# PIPELINE RUNNER
# ==================================================

def run():
    all_chunks = []

    docs = load_profile_documents()
    if not docs:
        raise RuntimeError("❌ No valid profile documents found.")

    for d in docs:
        chunks = profile_loader.build_profile_chunks(
            full_text=d["text"],
            source_file=d["source_file"]
        )
        all_chunks.extend(chunks)

    print(f"DEBUG: total profile chunks = {len(all_chunks)}")

    if not all_chunks:
        raise RuntimeError(
            "❌ No profile chunks generated. "
            "PDF likely has no usable text layer."
        )

    # =========================
    # EMBEDDING + FAISS
    # =========================

    vectors = [embed_text(c["text"]) for c in all_chunks]
    vectors_np = np.array(vectors, dtype="float32")

    dim = vectors_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors_np)

    faiss.write_index(index, str(PROFILE_VECTOR_DIR / "index.faiss"))

    with open(PROFILE_VECTOR_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Profile index built ({len(all_chunks)} chunks, dim={dim})")


if __name__ == "__main__":
    run()