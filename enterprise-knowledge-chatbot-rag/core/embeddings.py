# core/embeddings.py
import numpy as np
from api.embedding import embed_text  # SESUAI IMPLEMENTASI KAMU

def embed(text: str) -> np.ndarray:
    """
    Single source of truth for embeddings.

    - WAJIB dipakai untuk:
      - indexing
      - retrieval
    - Menghindari embedding mismatch
    """

    vec = embed_text(text)
    vec = np.array(vec).astype("float32")
    return vec


def normalize(vec: np.ndarray) -> np.ndarray:
    """
    Normalize vector for cosine similarity.
    """
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm
