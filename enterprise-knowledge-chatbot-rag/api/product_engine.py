# api/product_engine.py
import re
from typing import List

from api.search import search_products
from api.ollama import ask_ollama
from api.learning import save_pending


# =========================
# PRODUCT MEMORY (FOLLOW-UP)
# =========================
LAST_PRODUCTS = {}


# =========================
# PRODUCT ATTRIBUTE PARSER
# =========================
def extract_attributes_from_description(description: str):
    if not description:
        return {}

    text = description.lower()

    pattern = re.compile(
        r"(?P<name>[a-zA-Z\s]{3,30})\s*(?P<value>\d+)\s*(?P<unit>gram|mg|ml|kcal)",
        re.IGNORECASE
    )

    attributes = {}

    for match in pattern.finditer(text):
        name = match.group("name").strip()
        value = match.group("value")
        unit = match.group("unit")

        name = " ".join(name.split()[-2:])
        attributes[name] = f"{value} {unit}"

    return attributes


# =========================
# PRICE ANSWER
# =========================
def answer_price(products: List[dict]) -> str:
    if not products:
        return "Harga produk tidak ditemukan."

    if len(products) > 1:
        return (
            "Beberapa produk terkait:\n"
            + "\n".join(
                f"- {p['nama']} ({p['kode']}): Rp {p.get('harga','-')}"
                for p in products
            )
            + "\n\nSilakan sebutkan produk yang dimaksud."
        )

    p = products[0]
    return f"Harga {p['nama']} ({p['kode']}) adalah Rp {p.get('harga','-')}"


# =========================
# GENERAL FUNCTION ANSWER
# =========================
def answer_general_function(products: List[dict]) -> str:
    fungsi = {
        p.get("fungsi", "").strip()
        for p in products
        if p.get("fungsi")
    }

    if not fungsi:
        return (
            "Beberapa produk ditemukan:\n"
            + "\n".join(f"- {p.get('nama')} ({p.get('kode')})" for p in products)
            + "\n\nSilakan sebutkan salah satu produk untuk melihat fungsi secara detail."
        )

    result = "Secara umum, produk-produk ini memiliki fungsi:\n"
    for f in fungsi:
        result += f"- {f}\n"

    result += "\nProduk terkait:\n"
    result += "\n".join(
        f"- {p.get('nama')} ({p.get('kode')})" for p in products
    )

    result += "\n\nSilakan sebutkan produk tertentu jika ingin penjelasan lebih rinci."
    return result


# =========================
# SINGLE PRODUCT LLM
# =========================
def ask_product_llm(question: str, product: dict) -> str:
    info = product.get("fungsi") or product.get("deskripsi") or ""
    if not info.strip():
        info = "Informasi produk belum tersedia di database resmi."

    prompt = f"""
Anda adalah asisten produk resmi CNI Indonesia.

DATA PRODUK:
Nama: {product.get('nama')}
Kode: {product.get('kode')}
Harga: Rp {product.get('harga', '-')}

Deskripsi / Fungsi:
{info}

PERTANYAAN:
{question}
"""

    return ask_ollama(prompt, [product])


# =========================
# MAIN PRODUCT HANDLER
# =========================
def handle_product_flow(
    message: str,
    user_id: str,
    products_data: list
):
    q = message.lower().strip()

    products = search_products(message, products_data)

    # FOLLOW-UP TANPA NAMA PRODUK
    if not products and user_id in LAST_PRODUCTS and q in [
        "fungsi", "manfaat", "kegunaan",
        "harga", "berapa", "stok"
    ]:
        products = LAST_PRODUCTS[user_id]

    if not products:
        save_pending(message, user_id)
        return None, []

    LAST_PRODUCTS[user_id] = products

    # ATRIBUT DARI DESKRIPSI
    if len(products) == 1:
        desc = products[0].get("deskripsi", "")
        attrs = extract_attributes_from_description(desc)
        for attr, val in attrs.items():
            if attr in q:
                return (
                    f"{products[0]['nama']} ({products[0]['kode']}) "
                    f"mengandung {attr} sebesar {val}."
                ), products

    # HARGA
    if "harga" in q or "berapa" in q:
        return answer_price(products), products

    # FUNGSI
    if any(k in q for k in ["fungsi", "manfaat", "kegunaan"]):
        if len(products) > 1:
            return answer_general_function(products), products
        return ask_product_llm(message, products[0]), products

    # SINGLE PRODUCT DEFAULT
    if len(products) == 1:
        return ask_product_llm(message, products[0]), products

    # MULTI PRODUCT
    return (
        "Beberapa produk ditemukan:\n"
        + "\n".join(f"- {p['nama']} ({p['kode']})" for p in products)
        + "\n\nSilakan sebutkan produk yang dimaksud."
    ), products
