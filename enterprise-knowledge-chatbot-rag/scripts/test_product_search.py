# scripts/test_sop_search.py
from rag.retriever import search_sop

query = "coffee ginseng CNI no BPOM berapa?"

results = search_sop(query, top_k=3)

print("JUMLAH HASIL:", len(results))

for r in results:
    print("----")
    print("SECTION:", r.get("section"))
    print("TEXT:", r.get("text"))