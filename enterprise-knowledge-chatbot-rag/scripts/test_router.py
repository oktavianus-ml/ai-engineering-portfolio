from core.router import route_query

queries = [
    "bagaimana prosedur penanganan keluhan?",
    "apa visi dan misi perusahaan?",
    "ceritakan sejarah singkat CNI",
    "produk apa saja yang tersedia?",
    "berapa harga produk kesehatan?"
]

for q in queries:
    print(f"{q}  →  {route_query(q)}")