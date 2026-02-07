from knowledge.profile.retriever import ProfileRetriever

retriever = ProfileRetriever(top_k=3)

query = "apa visi dan misi perusahaan?"

results = retriever.retrieve(query)

print("\n=== RETRIEVER RESULTS ===\n")
for i, r in enumerate(results, 1):
    print(f"[{i}] {r['text'][:200]}\n")