# api/sop_engine.py
from typing import Tuple

from rag.retriever import search_sop
from rag.sop_llm import ask_sop_llm

from knowledge.profile.retriever import ProfileRetriever
from core.composer import compose_profile_answer

from api.learning import save_pending
from api.ollama import ask_ollama
from rag.call_llm import call_llm


# =========================
# PROFILE (fallback SOP)
# =========================
def _search_profile(query: str, top_k: int = 5):
    retriever = ProfileRetriever(top_k=top_k)
    return retriever.retrieve(query)


def _ask_profile_llm(query: str, contexts: list) -> str:
    return compose_profile_answer(query, contexts)


# =========================
# GENERAL LLM (LAST SOP RESORT)
# =========================
def _ask_general(question: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "Anda adalah asisten CNI Indonesia.\n\n"
                "ATURAN MUTLAK:\n"
                "- Jika pertanyaan berkaitan dengan profil resmi, sejarah, "
                "atau legal perusahaan, jawab:\n"
                "'Informasi resmi hanya tersedia di dokumen SOP perusahaan.'"
            )
        },
        {"role": "user", "content": question}
    ]
    return call_llm(messages, temperature=0.1)


# =========================
# MAIN SOP HANDLER
# =========================
def handle_sop_flow(query: str) -> Tuple[str | None, list]:
    """
    Return (answer, contexts)
    contexts dikembalikan kosong jika bukan SOP
    """

    # 1️⃣ SOP SEARCH
    contexts = search_sop(query, top_k=5)
    if contexts:
        return ask_sop_llm(query, contexts), contexts

    # 2️⃣ PROFILE FALLBACK
    profile_contexts = _search_profile(query, top_k=5)
    if profile_contexts:
        return _ask_profile_llm(query, profile_contexts), []

    # 3️⃣ SOP GENERAL
    return None, []