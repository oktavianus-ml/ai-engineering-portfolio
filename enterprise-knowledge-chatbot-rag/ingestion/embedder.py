import os
import json
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

from config import SOP_VECTOR_DIR


class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.metadata = []

    def embed_chunks(self, chunks):
        texts = [c["text"] for c in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        self.metadata = chunks

    def save(self):
        SOP_VECTOR_DIR.mkdir(parents=True, exist_ok=True)

        index_path = SOP_VECTOR_DIR / "index.faiss"
        meta_path = SOP_VECTOR_DIR / "metadata.json"

        faiss.write_index(self.index, str(index_path))
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

        print(f"💾 Vectorstore SOP disimpan ke {SOP_VECTOR_DIR}")

    def load(self):
        index_path = SOP_VECTOR_DIR / "index.faiss"
        meta_path = SOP_VECTOR_DIR / "metadata.json"

        self.index = faiss.read_index(str(index_path))
        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)