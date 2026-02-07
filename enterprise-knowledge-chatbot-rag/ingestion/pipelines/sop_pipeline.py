from typing import List, Dict
from pypdf import PdfReader
import json
import uuid
import requests
import numpy as np
import faiss
import re

from config import DATA_RAW_PDF_DIR, SOP_VECTOR_DIR

# ==================================================
# DOMAIN CONFIG — SOP ONLY
# ==================================================

SOP_SOURCE_DIR = DATA_RAW_PDF_DIR / "company sop profile"
SOP_VECTOR_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

# ==================================================
# EMBEDDING
# ==================================================

def embed_text(text: str) -> list:
    r = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    r.raise_for_status()
    return r.json()["embedding"]

# ==================================================
# STEP 1 — LOAD PDF
# ==================================================

def load_sop_documents() -> List[Dict]:
    docs = []

    #for pdf_path in SOP_SOURCE_DIR.glob("*.pdf"):
    for pdf_path in SOP_SOURCE_DIR.glob("*.pdf"):
        if pdf_path.name.lower() != "sop_cs_cni.pdf":
            continue
        reader = PdfReader(pdf_path)
        pages = [
            page.extract_text().strip()
            for page in reader.pages
            if page.extract_text()
        ]

        full_text = "\n\n".join(pages)

        if len(full_text) < 500:
            print(f"⚠️ Skipped (too short): {pdf_path.name}")
            continue

        docs.append({
            "source_file": pdf_path.name,
            "text": full_text
        })

        print(f"✅ Loaded SOP: {pdf_path.name}")

    return docs

# ==================================================
# STEP 2 — SECTION SPLIT
# ==================================================

SECTION_PATTERN = r"(BAB\s+[IVXLC]+|PASAL\s+\d+|\n[A-Z][A-Z\s]{3,}\n)"

def split_by_section(text: str):
    """
    Split SOP by numbered headings like:
    1. PROFIL PERUSAHAAN
    2. VISI DAN MISI
    ...
    """
    pattern = re.compile(r"\n(\d+\.\s+[A-Z][A-Z\s]+)\n")
    matches = list(pattern.finditer(text))
    sections = []

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        title = m.group(1).strip()
        body = text[start:end].strip()

        if len(body) < 30:
            continue

        sections.append((title, body))

    return sections

# ==================================================
# STEP 3 — BUILD SOP CHUNKS
# ==================================================

def build_sop_chunks(documents: List[Dict], max_words: int = 400) -> List[Dict]:
    chunks = []

    for doc in documents:
        for section, text in split_by_section(doc["text"]):
            words = text.split()

            for i in range(0, len(words), max_words):
                chunk_text = " ".join(words[i:i + max_words]).strip()
                if not chunk_text:
                    continue

                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "source_file": doc["source_file"],
                    "section": section,
                    "text": chunk_text
                })

    print(f"✅ SOP chunks created: {len(chunks)}")
    return chunks

# ==================================================
# STEP 4 — METADATA ENRICH
# ==================================================

def detect_function(text: str) -> str:
    t = text.lower()
    if "refund" in t:
        return "refund"
    if "komplain" in t or "complaint" in t:
        return "complaint"
    if "eskalasi" in t:
        return "escalation"
    if "visi" in t or "misi" in t:
        return "vision_mission"
    return "general"

def enrich_chunks(chunks: List[Dict]) -> List[Dict]:
    enriched = []

    for c in chunks:
        function = detect_function(c["text"])

        enriched.append({
            "domain": "sop",
            "doc_id": f"SOP-CS-{function.upper()}",
            "doc_type": "SOP",
            "function": function,
            "version": "v1.0",
            "effective_date": "2026-01-01",
            "status": "active",
            "owner": "Customer Service",
            "confidentiality": "internal",
            **c
        })

    return enriched

# ==================================================
# STEP 5 — EMBED + STORE
# ==================================================

def embed_and_store(chunks: List[Dict]):
    vectors = [embed_text(c["text"]) for c in chunks]
    vectors_np = np.array(vectors).astype("float32")

    index = faiss.IndexFlatL2(vectors_np.shape[1])
    index.add(vectors_np)

    faiss.write_index(index, str(SOP_VECTOR_DIR / "index.faiss"))

    with open(SOP_VECTOR_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ FAISS index stored ({len(chunks)} chunks)")

# ==================================================
# PIPELINE RUNNER
# ==================================================

def run():
    docs = load_sop_documents()
    chunks = build_sop_chunks(docs)
    enriched = enrich_chunks(chunks)
    embed_and_store(enriched)

if __name__ == "__main__":
    run()