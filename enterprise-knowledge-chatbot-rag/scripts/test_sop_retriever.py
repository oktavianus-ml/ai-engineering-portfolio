from knowledge.sop.retriever import SOPRetriever

retriever = SOPRetriever(top_k=5)

query = "bagaimana prosedur keluhan?"

results = retriever.retrieve(query)

if not results:
    print("❌ SOP terkait keluhan tidak ditemukan.")
else:
    for r in results:
        print(
            r["doc_id"],
            r["function"],
            r.get("section", "N/A")
        )