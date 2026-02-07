# core/engine.py
"""
Core Engine
===========

Engine ini berfungsi sebagai:
1. Single entry-point untuk menjawab pertanyaan user
2. Adapter agar function-based engine bisa dipakai sebagai object
3. Bridge antara router, retriever, dan composer

⚠️ Engine TIDAK melakukan retrieval detail secara langsung,
melainkan mengorkestrasi flow berdasarkan domain.
"""

from core.router import route_query

from knowledge.sop.retriever import SOPRetriever
from knowledge.profile.retriever import ProfileRetriever

from core.composer import (
    compose_sop_answer,
    compose_profile_answer,
    compose_general_answer,
)


# ======================================================
# FUNCTION-BASED ENGINE (PURE LOGIC)
# ======================================================
def answer_query(query: str) -> str:
    """
    Main logic untuk menjawab pertanyaan user berdasarkan domain.

    Alur:
    - Router menentukan domain (sop / profile / product / general)
    - Retriever mengambil knowledge sesuai domain
    - Composer merangkai jawaban akhir
    """

    domain = route_query(query)

    # =========================
    # SOP DOMAIN
    # =========================
    if domain == "sop":
        retriever = SOPRetriever(top_k=5)
        results = retriever.retrieve(query)

        # 🔁 Smart fallback:
        # Jika SOP tidak ketemu, coba Profile sebelum ke General
        if not results:
            profile_retriever = ProfileRetriever(top_k=5)
            profile_results = profile_retriever.retrieve(query)

            if profile_results:
                return compose_profile_answer(query, profile_results)

            return compose_general_answer(query)

        return compose_sop_answer(query, results)

    # =========================
    # PROFILE DOMAIN
    # =========================
    if domain == "profile":
        retriever = ProfileRetriever(top_k=5)
        results = retriever.retrieve(query)
        return compose_profile_answer(query, results)

    # =========================
    # PRODUCT DOMAIN
    # =========================
    # Placeholder — product handled by product_engine / RAG
    if domain == "product":
        return "Informasi produk sedang dalam pengembangan."

    # =========================
    # GENERAL FALLBACK
    # =========================
    return compose_general_answer(query)


# ======================================================
# ENGINE ADAPTER (OBJECT INTERFACE)
# ======================================================
class Engine:
    """
    Engine Adapter

    Tujuan:
    - Membungkus function-based engine agar bisa dipakai sebagai object
    - Digunakan oleh:
        - FastAPI
        - Chat Engine
        - RAG bridge

    Catatan:
    - Logic utama tetap ada di answer_query()
    - Class ini bersifat tipis (thin adapter)
    """

    def answer(self, query: str) -> str:
        """
        Public method untuk menjawab pertanyaan user.

        Args:
            query (str): pertanyaan user

        Returns:
            str: jawaban akhir
        """
        return answer_query(query)
