from typing import List, Dict
from pathlib import Path
from pypdf import PdfReader
import json
import uuid

from config import DATA_RAW_PDF_DIR, VECTORSTORE_DIR

NEWS_SOURCE_DIR = DATA_RAW_PDF_DIR / "news"
NEWS_VECTOR_DIR = VECTORSTORE_DIR / "news"
NEWS_VECTOR_DIR.mkdir(parents=True, exist_ok=True)


def load_news_documents() -> List[Dict]:
    docs = []

    for pdf in NEWS_SOURCE_DIR.glob("*.pdf"):
        reader = PdfReader(pdf)
        pages = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())

        full_text = "\n\n".join(pages)
        if len(full_text) < 300:
            continue

        docs.append({
            "source_file": pdf.name,
            "text": full_text
        })

    return docs


def chunk_news(docs: List[Dict], chunk_size=600) -> List[Dict]:
    chunks = []

    for doc in docs:
        words = doc["text"].split()
        for i in range(0, len(words), chunk_size):
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "text": " ".join(words[i:i+chunk_size]),
                "source_file": doc["source_file"]
            })

    return chunks


def attach_metadata(chunks: List[Dict]) -> List[Dict]:
    enriched = []

    for c in chunks:
        enriched.append({
            "domain": "news",
            "doc_type": "NEWS",
            "status": "active",
            "source_file": c["source_file"],
            "chunk_id": c["chunk_id"],
            "text": c["text"]
        })

    return enriched


def run():
    docs = load_news_documents()
    chunks = chunk_news(docs)
    enriched = attach_metadata(chunks)

    with open(NEWS_VECTOR_DIR / "metadata.json", "w") as f:
        json.dump(enriched, f, indent=2)


if __name__ == "__main__":
    run()