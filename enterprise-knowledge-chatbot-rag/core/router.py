# core/router.py
from typing import Literal

# Domain yang dikenali oleh sistem
Domain = Literal["sop", "profile", "product", "general"]

# ==================================================
# KEYWORDS CONFIG
# ==================================================
# Semua keyword di bawah ini:
# - lowercase
# - berbasis substring (bukan regex)
# - dipakai untuk routing cepat & deterministik
#
# ⚠️ IMPORTANT:
# Urutan pengecekan domain MATTERS.
# Keyword bisa overlap, jadi prioritas harus eksplisit.

# SOP = prosedur / kebijakan operasional
SOP_KEYWORDS = [
    "keluhan", "komplain", "pengaduan",
    "prosedur", "alur", "eskalasi",
    "refund", "retur", "pengembalian",
    "customer service", "cs"
]

# PROFILE = identitas & informasi resmi perusahaan
PROFILE_KEYWORDS = [
    "profil", "tentang perusahaan", "tentang cni",
    "visi", "misi", "sejarah",
    "corporate", "company profile"
]

# PRODUCT = informasi produk & transaksi
PRODUCT_KEYWORDS = [
    "produk", "product",
    "harga", "price",
    "manfaat", "benefit",
    "komposisi", "kandungan",
    "stok", "tersedia",
    "fungsi",          # ✅ INI KUNCI
]


def _contains_any(text: str, keywords: list[str]) -> bool:
    """
    Helper kecil untuk menjaga keterbacaan.
    Mengembalikan True jika salah satu keyword
    muncul sebagai substring di text.
    """
    return any(k in text for k in keywords)


def route_query(query: str) -> Domain:
    """
    Menentukan domain handler untuk sebuah query user.

    Prinsip desain:
    - Rule-based (bukan AI) → predictable & audit-friendly
    - Cepat (string check saja)
    - Deterministik (tidak bergantung konteks)
    - Domain dipilih SEKALI di awal pipeline

    PRIORITY ORDER (PENTING):
    1. SOP      → prosedur & kebijakan (paling ketat)
    2. PROFILE  → info resmi perusahaan
    3. PRODUCT  → info produk & harga
    4. GENERAL  → fallback

    Contoh:
    - "cara komplain"         → sop
    - "visi dan misi cni"     → profile
    - "harga produk A"        → product
    """

    q = query.lower().strip()

    # ==================================================
    # 1️⃣ SOP (HARUS PALING AWAL)
    # ==================================================
    # SOP harus dicek dulu karena:
    # - menyangkut kebijakan & compliance
    # - tidak boleh ketimpa domain lain
    if _contains_any(q, SOP_KEYWORDS):
        return "sop"

    # ==================================================
    # 2️⃣ PROFILE (IDENTITAS PERUSAHAAN)
    # ==================================================
    # Profile dicek sebelum product agar:
    # "visi misi perusahaan" tidak salah masuk product
    if _contains_any(q, PROFILE_KEYWORDS):
        return "profile"

    # ==================================================
    # 3️⃣ PRODUCT (INFO PRODUK)
    # ==================================================
    if _contains_any(q, PRODUCT_KEYWORDS):
        return "product"

    # ==================================================
    # 4️⃣ GENERAL (FALLBACK)
    # ==================================================
    return "general"
