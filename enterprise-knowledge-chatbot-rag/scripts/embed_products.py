import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# =========================
# PATH CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "json")

PRODUCT_FILE = os.path.join(DATA_DIR, "products.json")
VECTOR_DIR = os.path.join(DATA_DIR, "vector_store", "products")

INDEX_FILE = os.path.join(VECTOR_DIR, "index.faiss")
META_FILE = os.path.join(VECTOR_DIR, "metadata.json")

os.makedirs(VECTOR_DIR, exist_ok=True)

# =========================
# LOAD MODEL
# =========================
print("🔄 Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# =========================
# LOAD PRODUCTS
# =========================
if not os.path.exists(PRODUCT_FILE):
    raise FileNotFoundError(f"products.json tidak ditemukan di {PRODUCT_FILE}")

with open(PRODUCT_FILE, encoding="utf-8") as f:
    products = json.load(f)

if not products:
    raise ValueError("products.json kosong")

texts = []
metadata = []

# =========================
# HELPER (ANTI NONE)
# =========================
def safe(val, fallback="Informasi belum tersedia."):
    if val is None:
        return fallback
    val = str(val).strip()
    return val if val else fallback


# =========================
# BUILD SEMANTIC TEXT (INTI RAG)
# =========================
for p in products:
    nama = safe(p.get("nama"), "")
    kode = safe(p.get("kode"), "")
    fungsi = safe(p.get("fungsi"))
    deskripsi = safe(p.get("deskripsi"))

    # 🆕 ALIAS SUPPORT (MINIMAL)
    alias = p.get("alias", {})
    alias_nama = alias.get("nama", [])
    alias_kode = alias.get("kode", [])

    alias_text = ""
    if alias_nama or alias_kode:
        alias_text = f"""
Alias produk:
Nama lain: {", ".join(alias_nama) if alias_nama else "-"}
Kode lain: {", ".join(alias_kode) if alias_kode else "-"}
"""

    text = f"""
Produk resmi CNI Indonesia.

Nama produk: {nama}
Kode produk: {kode}

{nama} adalah produk suplemen kesehatan dari CNI Indonesia.
Produk ini adalah PRODUK CNI,
bukan aplikasi digital, bukan platform UMKM,
dan bukan layanan teknologi.

Fungsi utama produk:
{fungsi}

Deskripsi produk:
{deskripsi}

{alias_text}

Kategori: Produk kesehatan CNI.

Jika pengguna bertanya tentang "{nama}", aliasnya,
atau kode "{kode}",
yang dimaksud adalah PRODUK CNI ini.
"""

    texts.append(text.strip())

    metadata.append({
        "kode": kode,
        "nama": nama,
        "text": text.strip(),
        "type": "product",
        "brand": "CNI"
    })

# =========================
# EMBEDDING
# =========================
print("🔄 Membuat embedding...")
embeddings = model.encode(texts, convert_to_numpy=True)

if embeddings.size == 0:
    raise ValueError("Embedding kosong")

dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

# =========================
# SAVE VECTOR STORE
# =========================
faiss.write_index(index, INDEX_FILE)

with open(META_FILE, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

# =========================
# LOG
# =========================
print("✅ Embedding produk CNI selesai")
print("Total produk:", len(metadata))
print("FAISS index size:", index.ntotal)
print("Vector store path:", VECTOR_DIR)
