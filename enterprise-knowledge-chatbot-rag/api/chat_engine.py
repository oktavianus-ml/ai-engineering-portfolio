import json
from typing import Tuple

from api.search import search_products
from api.ollama import ask_ollama
from api.learning import get_learned_answer, save_pending

from core.router import route_query
from core.engine import Engine
from core.composer import CSComposer

from knowledge.products.retriever import ProductRetriever
from knowledge.profile.retriever import ProfileRetriever

from api.product_engine import handle_product_flow
from api.sop_engine import handle_sop_flow
from api.profile_engine import handle_profile_flow
from api.general_engine import handle_general_flow
from core.context_builder import ContextBuilder
from core.confidence import log_confidence_event



print("🔥 CHAT_ENGINE CLEAN VERSION LOADED 🔥")

# =========================
# INIT RAG
# =========================
#rag_engine = Engine()
context_builder = ContextBuilder() # ✅ BARU
rag_composer = CSComposer()

product_retriever = ProductRetriever()
profile_retriever = ProfileRetriever()

# =========================
# USER MEMORY (FOLLOW-UP)
# =========================
USER_LAST_PRODUCTS = {}


# =========================
# RAG HANDLER
# =========================
def _handle_rag(message: str):
    docs = product_retriever.retrieve(message)
    if not docs:
        return None

    context = context_builder.build(docs)
    if not context:
        return None

    # =========================
    # 🛠️ CLEAN CONTEXT (PRODUCT)
    # =========================
    cleaned_lines = []

    for line in context.splitlines():
        l = line.strip()
        if not l:
            continue

        l_lower = l.lower()

        # ❌ buang footer / header / navigasi web
        if any(x in l_lower for x in [
            "empowering your tomorrow",
            "contact us",
            "hak cipta",
            "copyright",
            "building",
            "home about",
            "news articles",
            "follow information",
            "syarat & ketentuan",
            "kebijakan & privasi",
            "©"
        ]):
            continue

        # ❌ buang produk lain (biar fokus)
        if "cni ginseng" in l_lower:
            continue

        cleaned_lines.append(l)

    if not cleaned_lines:
        return None

    cleaned_context = "\n".join(cleaned_lines)

    # =========================
    # ✂️ BATASI PANJANG (UX)
    # =========================
    return cleaned_context[:1200]


# =========================
# HELPER CONFIDENCE LABELING

def confidence_label(score: float) -> str:
    if score >= 0.75:
        return "tinggi"
    if score >= 0.60:
        return "sedang"
    return "rendah"





# =========================
# MAIN CHAT ENGINE (SATU PINTU)
# =========================
def handle_chat_engine(
    message: str,
    user_id: str = "anonymous",
    platform: str | None = None,
    products_data: list | None = None
) -> Tuple[str, list]:

    msg = message.lower().strip()

    # 1️⃣ LEARNED ANSWER
    learned = get_learned_answer(message, user_id)
    if learned:
        return learned, []

    # 2️⃣ FOLLOW-UP TANPA PRODUK
    if msg in ["harga", "berapa", "harganya"] and user_id in USER_LAST_PRODUCTS:
        matches = USER_LAST_PRODUCTS[user_id]
        answer = ask_ollama(message, matches, user_id)
        return answer, matches

    # 3️⃣ PRODUCT FLOW (always first, deterministic)
    product_answer, products = handle_product_flow(
        message=message,
        user_id=user_id,
        products_data=products_data
    )

    if product_answer is not None:
        return product_answer, products or []


    # =========================
    # DOMAIN ROUTING (KUNCI)
    # =========================
    domain = route_query(message)

    # 4️⃣ PROFILE (OFFICIAL INFO)
    if domain == "profile":
        profile_answer, _ = handle_profile_flow(message)
        if profile_answer:
            return profile_answer, []

    # 5️⃣ SOP (PROCEDURAL ONLY)
    if domain == "sop":
        sop_answer, _ = handle_sop_flow(message)
        if sop_answer:
            return sop_answer, []
        


    # 6️⃣ PRODUCT RAG (CONFIDENCE-AWARE)
    if domain == "product":
        print("🔥 CONFIDENCE-AWARE RAG TRIGGERED 🔥")

        # --------------------------------
        # RETRIEVE PRODUCT KNOWLEDGE
        # --------------------------------
        results = product_retriever.retrieve(message, with_score=True)

        # --------------------------------
        # NO DATA → SAFE ABSTAIN
        # --------------------------------
        if not results:
            return (
                "Untuk memastikan informasi yang akurat, "
                "kami perlu melakukan pengecekan lebih lanjut terlebih dahulu."
            ), []

        # --------------------------------
        # TOP SCORE
        # --------------------------------
        top_score = results[0][1]
        print("🎯 TOP SCORE:", round(top_score, 3))

        # --------------------------------
        # CONFIDENCE POLICY
        # --------------------------------
        HIGH_CONF = 0.75
        MEDIUM_CONF = 0.60

        # --------------------------------
        # BUILD CONTEXT (ONCE)
        # --------------------------------
        context = context_builder.build([r[0] for r in results])

        # --------------------------------
        # CONFIDENCE LABEL
        # --------------------------------
        label = confidence_label(top_score)

        # --------------------------------
        # STEP 2 — CONFIDENCE LOGGING
        # --------------------------------
        log_confidence_event(
            query=message,
            score=top_score,
            label=label,
            domain="product"
        )

        # --------------------------------
        # HIGH CONFIDENCE
        # --------------------------------
        if top_score >= HIGH_CONF:
            answer = (
                f"(Tingkat keyakinan: {label})\n\n"
                + rag_composer.compose_product_answer(
                    query=message,
                    context=context
                )
            )
            return answer, []

        # --------------------------------
        # MEDIUM CONFIDENCE
        # --------------------------------
        if top_score >= MEDIUM_CONF:
            answer = (
                f"(Tingkat keyakinan: {label})\n\n"
                "Berdasarkan informasi yang tersedia, berikut penjelasannya:\n\n"
                + rag_composer.compose_product_answer(
                    query=message,
                    context=context
                )
            )
            return answer, []

        # --------------------------------
        # LOW CONFIDENCE → ESCALATE
        # --------------------------------
        save_pending(message, user_id)

        return (
            "Maaf, saya belum dapat memahami maksud pertanyaan Anda. "
            "Silakan tuliskan pertanyaan dengan lebih jelas atau sertakan "
            "nama produk yang ingin ditanyakan.",
            []
        )
    
    print("⚠️ FINAL FALLBACK RETURN (NO DOMAIN MATCHED)")

    return (
        "Maaf, saya belum bisa memahami maksud pertanyaan Anda. "
        "Silakan tuliskan pertanyaan dengan lebih jelas atau sertakan "
        "nama produk yang ingin ditanyakan.",
        []
    )