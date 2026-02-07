# ingestion/ingest_pdf.py
import os
from pypdf import PdfReader
from ingestion.chunker import chunk_text
from ingestion.embedder import Embedder
from config import DATA_RAW_PDF_DIR

def load_pdf(path: str) -> str:
    reader = PdfReader(path)
    texts = []

    for page in reader.pages:
        if page.extract_text():
            texts.append(page.extract_text())

    return "\n".join(texts)


def ingest_all_pdfs():
    all_chunks = []

    for file in os.listdir(DATA_RAW_PDF_DIR):
        if file.lower().endswith(".pdf"):
            path = os.path.join(DATA_RAW_PDF_DIR, file)
            print(f"📄 Processing {file}")

            text = load_pdf(path)

            chunks = chunk_text(
                text=text,
                source=file,
                doc_type="pdf"
            )

            all_chunks.extend(chunks)

    print(f"✂️ Total chunks: {len(all_chunks)}")

    embedder = Embedder()
    embedder.embed_chunks(all_chunks)
    embedder.save()

    print("✅ PDF embedding selesai")


if __name__ == "__main__":
    ingest_all_pdfs()