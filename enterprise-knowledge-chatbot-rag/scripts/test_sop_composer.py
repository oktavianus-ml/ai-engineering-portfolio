from knowledge.sop.retriever import SOPRetriever
from core.composer import compose_sop_answer

retriever = SOPRetriever(top_k=5)

query = "bagaimana prosedur keluhan?"

results = retriever.retrieve(query)

answer = compose_sop_answer(query, results)

print("\n=== FINAL ANSWER ===\n")
print(answer)