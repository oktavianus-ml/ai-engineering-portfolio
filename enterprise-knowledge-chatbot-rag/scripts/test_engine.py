from core.engine import answer_query

queries = [
    "bagaimana prosedur penanganan keluhan?",
    "apa visi dan misi perusahaan?",
    "ceritakan sejarah singkat CNI"
]

for q in queries:
    print("\nQ:", q)
    print("A:", answer_query(q))
    print("A:", answer_query(q))