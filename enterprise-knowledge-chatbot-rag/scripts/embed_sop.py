import os
from dotenv import load_dotenv
import json
import faiss   
import numpy as np
from sentence_transformers import SentenceTransformer

load_dotenv()

from api.loaders.pdf_loader import load_pdf
from ingestion.chunker import chunk_pdf_page


# =========================
# CONFIG
# =========================
# =========================
# CONFIG
# =========================
MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
PDF_DIR = os.getenv("PDF_DIR", "data/raw/pdf")
OUT_DIR = os.getenv(
    "SOP_VECTOR_DIR",
    "data/json/vector_store/sop_customer_service"
)

os.makedirs(OUT_DIR, exist_ok=True)

MODEL = SentenceTransformer(MODEL_NAME)


# =========================
# BUILD VECTOR STORE
# =========================
def build_sop_vectorstore(pdf_paths: list[str]):
    all_chunks = []

    for pdf_path in pdf_paths:
        print(f"📄 Processing: {pdf_path}")
        pages = load_pdf(pdf_path)

        if not pages:
            print(f"⚠️ PDF kosong atau gagal dibaca: {pdf_path}")
            continue

        for p in pages:
            chunks = chunk_pdf_page(
                text=p["text"],
                source=os.path.basename(pdf_path),
                page=p["page"]
            )
            all_chunks.extend(chunks)

    if not all_chunks:
        print("❌ Tidak ada chunk SOP yang diproses.")
        return

    texts = [c["text"] for c in all_chunks]
    embeddings = MODEL.encode(texts, show_progress_bar=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    faiss.write_index(index, os.path.join(OUT_DIR, "index.faiss"))

    with open(os.path.join(OUT_DIR, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ SOP vector store dibuat dari {len(pdf_paths)} PDF → {len(all_chunks)} chunks")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    pdf_files = [
        os.path.join(PDF_DIR, f)
        for f in os.listdir(PDF_DIR)
        if f.lower().endswith(".pdf")
    ]

    build_sop_vectorstore(pdf_files)