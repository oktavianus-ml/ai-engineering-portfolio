import re
from api.ollama import ask_ollama
from api.ollama import call_llm  

# =========================
# INTENT DETECTION
# =========================
def detect_intent(query: str) -> str:
    """
    Mendeteksi intent utama dari pertanyaan user secara rule-based.
    Dibuat ringan dan deterministik agar cepat dan stabil.
    """
    q = query.lower().strip()

    # Pemetaan intent ke kata kunci yang sering digunakan user
    INTENT_MAP = {
        # Keluhan atau komplain pelanggan
        "complaint": ["keluhan", "komplain", "pengaduan"],

        # Visi, misi, atau tujuan perusahaan
        "vision": ["visi", "misi", "tujuan perusahaan"],

        # Informasi umum tentang profil perusahaan
        "profile": ["profil", "tentang perusahaan", "sejarah"],
    }

    # Cek intent berdasarkan kemunculan keyword
    for intent, keywords in INTENT_MAP.items():
        if any(k in q for k in keywords):
            return intent

    # Jika tidak ada intent yang cocok, gunakan general
    return "general"


# =========================
# HUMAN-FRIENDLY LABEL
# =========================
# Digunakan sebagai judul jawaban agar mudah dipahami user
FUNCTION_LABELS = {
    "complaint": "Prosedur Penanganan Keluhan",
    "vision_mission": "Visi dan Misi Perusahaan",
    "general": "Informasi Umum Perusahaan",
}


# =========================
# CONTENT FILTER RULES
# =========================
# Aturan ini membantu memilih potongan SOP yang paling relevan
# dan menghindari konten yang tidak sesuai dengan intent user
FILTER_RULES = {
    "complaint": {
        "include": ["keluhan", "komplain", "penanganan", "alur", "eskalasi"],
        "exclude": ["visi", "misi", "profil", "sejarah", "about us"],
    },
    "vision": {
        "include": ["visi", "misi"],
        "exclude": [],
    },
    "profile": {
        "include": ["profil", "sejarah", "perusahaan"],
        "exclude": [],
    },
    # General digunakan sebagai fallback tanpa filter khusus
    "general": {
        "include": [],
        "exclude": [],
    },
}


# =========================
# ANSWER COMPOSER (SOP)
# =========================
def compose_sop_answer(query: str, sop_chunks: list) -> str:
    """
    Menyusun jawaban berbasis SOP yang relevan dengan intent user.
    Fokus pada kejelasan dan kemudahan dipahami, bukan menampilkan dokumen mentah.
    """

    # Jika tidak ada SOP yang bisa digunakan
    if not sop_chunks:
        return (
            "Maaf, informasi yang relevan tidak ditemukan "
            "pada SOP yang tersedia."
        )

    # Deteksi intent user untuk menentukan aturan filter
    intent = detect_intent(query)
    rules = FILTER_RULES.get(intent, FILTER_RULES["general"])

    # Ambil fungsi SOP utama dari chunk pertama
    raw_function = sop_chunks[0].get("function", "general")

    # Mapping function ke judul yang ramah untuk user
    title = FUNCTION_LABELS.get(
        raw_function,
        raw_function.replace("_", " ").title()
    )

    selected = []

    for chunk in sop_chunks:
        text = chunk.get("text", "").strip()
        if not text:
            continue

        text_lower = text.lower()

        # ❌ Buang konten yang tidak relevan lebih dulu (exclude)
        if rules["exclude"] and any(k in text_lower for k in rules["exclude"]):
            continue

        # ✅ Pilih konten yang sesuai dengan intent (include)
        if rules["include"]:
            if any(k in text_lower for k in rules["include"]):
                selected.append(text)
        else:
            selected.append(text)

    # =========================
    # FALLBACK (ANTI KOSONG)
    # =========================
    # Jika hasil filter kosong, ambil konten berdasarkan function SOP
    if not selected:
        selected = [
            c.get("text", "").strip()
            for c in sop_chunks
            if c.get("function") == raw_function and c.get("text")
        ]

    # Batasi maksimal 3 poin agar jawaban tetap ringkas
    selected = selected[:3]

    body = "\n".join(f"- {s}" for s in selected)

    return f"""
Berikut adalah **{title}** sesuai ketentuan yang berlaku:

{body}
""".strip()


# =========================
# PROFILE ANSWER COMPOSER
# =========================
# =========================
# PROFILE ANSWER COMPOSER
# =========================
def compose_profile_answer(query: str, chunks: list) -> str:
    """
    Menyusun jawaban profil perusahaan yang:
    - Ringkas
    - Relevan dengan pertanyaan user
    - Menghindari dumping dokumen
    - Bergaya Customer Service manusia
    """

    # Guard: tidak ada data profile
    if not chunks:
        return "Maaf, informasi profil perusahaan belum tersedia."

    q = query.lower().strip()

    # =========================
    # DETECT INTENT RINGAN
    # =========================
    is_founding = any(k in q for k in ["didirikan", "berdiri", "tahun"])
    is_vision   = any(k in q for k in ["visi", "misi"])
    is_history  = any(k in q for k in ["sejarah", "perjalanan"])

    # ==================================================
    # KHUSUS: PERTANYAAN "DIDIRIKAN KAPAN"
    # ==================================================
    # Untuk pertanyaan fakta, JANGAN pilih chunk dulu.
    # Scan semua teks dan ekstrak tanggal / tahun.
    if is_founding:
        full_text = " ".join(
            c.get("text", "").replace("\n", " ")
            for c in chunks
            if c.get("text")
        )

        # PRIORITAS 1: tanggal lengkap
        date_match = re.search(
            r"(\d{1,2}\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+\d{4})",
            full_text,
            re.IGNORECASE
        )

        if date_match:
            return (
                f"CNI didirikan pada {date_match.group(1)}.\n\n"
                "Jika ingin, saya bisa jelaskan lebih lanjut "
                "tentang sejarah, visi misi, atau profil perusahaan."
            )

        # PRIORITAS 2: tahun saja (BERSIH)
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", full_text)
        if year_match:
            return (
                f"CNI didirikan pada tahun {year_match.group(1)}.\n\n"
                "Jika ingin, saya bisa jelaskan lebih lanjut "
                "tentang sejarah, visi misi, atau profil perusahaan."
            )


    # =========================
    # PILIH TEKS PALING RELEVAN
    # =========================
    # Dipakai untuk visi / sejarah / fallback umum
    selected_text = ""

    for c in chunks:
        text = c.get("text", "").strip().replace("\n", " ")
        if not text:
            continue

        t = text.lower()

        # Visi & misi
        if is_vision and any(k in t for k in ["visi", "misi"]):
            selected_text = text
            break

        # Sejarah / perjalanan
        if is_history and any(k in t for k in ["sejak", "berdiri", "perjalanan"]):
            selected_text = text
            break

    # =========================
    # FALLBACK AMAN
    # =========================
    # Jika tidak ada yang match, ambil chunk pertama
    if not selected_text:
        selected_text = chunks[0].get("text", "").strip()

    # =========================
    # RINGKAS KALIMAT (AMAN DARI "PT.")
    # =========================
    # Split pakai ". " (titik + spasi) supaya "PT." tidak terpotong
    sentences = [
        s.strip()
        for s in selected_text.split(". ")
        if len(s.strip()) > 20  # buang fragmen terlalu pendek
    ]

    # Batasi panjang agar UX tetap enak
    summary = sentences[0] + "." if sentences else selected_text

    return (
        f"{summary}\n\n"
        "Jika ingin, saya bisa jelaskan lebih lanjut "
        "tentang sejarah, visi misi, atau profil perusahaan."
    )


# =========================
# GENERAL / FALLBACK COMPOSER
# =========================
def compose_general_answer(query: str) -> str:
    """
    Jawaban fallback saat intent atau domain belum jelas.
    Bertujuan mengarahkan user agar pertanyaannya lebih spesifik.
    """
    return (
        "Maaf, saya belum yakin informasi apa yang Anda maksud.\n\n"
        "Anda bisa mencoba menanyakan:\n"
        "- Prosedur atau keluhan pelanggan\n"
        "- Profil, visi, atau misi perusahaan\n"
        "- Informasi produk\n"
    )

# =========================
# COMPOSER ADAPTER (COMPAT)
# =========================
class CSComposer:
    """
    Adapter agar composer function-based
    bisa dipakai sebagai object (FastAPI / RAG bridge).
    """

    # -------------------------
    # LEGACY COMPOSER (JANGAN DIUBAH)
    # -------------------------
    def compose(self, question: str, context: str) -> str:
        """
        Composer lama.
        Dipertahankan untuk backward compatibility.
        """
        return context


    # -------------------------
    # NEW: PRODUCT COMPOSER
    # -------------------------
    def compose_product_answer(
        self,
        query: str,
        context: str
    ) -> str:
        """
        Execute RAG answer using raw textual context.
        """

        prompt = f"""
    Gunakan informasi berikut untuk menjawab pertanyaan customer.

    INFORMASI:
    {context}

    PERTANYAAN:
    {query}

    Jawab secara profesional dan jelas.
    """.strip()

        return call_llm(prompt)
