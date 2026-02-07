# api/profile_engine.py
from typing import Tuple

from knowledge.profile.retriever import ProfileRetriever
from core.composer import compose_profile_answer


# =========================
# PROFILE HANDLER
# =========================
def handle_profile_flow(
    query: str,
    top_k: int = 5
) -> Tuple[str | None, list]:
    """
    Return (answer, contexts)
    """

    retriever = ProfileRetriever(top_k=top_k)
    contexts = retriever.retrieve(query)

    if not contexts:
        return None, []

    answer = compose_profile_answer(query, contexts)
    return answer, contexts
