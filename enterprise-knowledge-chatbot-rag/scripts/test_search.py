import faiss
import json
from sentence_transformers import SentenceTransformer

INDEX_FILE = "data/json/vector_store/index.faiss"
META_FILE = "data/json/vector_store/metadata.json"

model = SentenceTransformer("all-MiniLM-L6-v2")

index = faiss.read_index(INDEX_FILE)
with open(META_FILE, "r", encoding="utf-8") as f:
    metadata = json.load(f)

query = "Apa manfaat CNI Ginseng Coffee?"
q_emb = model.encode([query])

D, I = index.search(q_emb, k=3)

for idx in I[0]:
    print("----")
    print(metadata[idx]["text"][:300])