import faiss
import json
import numpy as np
import requests
from config import SOP_VECTOR_DIR

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


def embed(text):
    r = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBED_MODEL, "prompt": text}
    )
    return r.json()["embedding"]


index = faiss.read_index(str(SOP_VECTOR_DIR / "index.faiss"))

with open(SOP_VECTOR_DIR / "metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

query = "bagaimana prosedur keluhan?"

q_vec = np.array([embed(query)]).astype("float32")

# DEBUGGING INFO
print("Index dimension:", index.d)
print("Query vector dimension:", q_vec.shape[1])
# Perform the search

D, I = index.search(q_vec, k=3)

for idx in I[0]:
    print(metadata[idx]["doc_id"], metadata[idx]["function"])