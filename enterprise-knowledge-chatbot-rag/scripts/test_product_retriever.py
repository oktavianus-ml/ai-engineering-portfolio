from knowledge.products.retriever import ProductRetriever

def main():
    retriever = ProductRetriever(top_k=5)

    query = "Apa itu CNI Ginseng Coffee?"
    product_name = "cni ginseng coffee"

    results = retriever.retrieve(
        query=query,
        product_name=product_name
    )

    print(f"Query        : {query}")
    print(f"Product lock : {product_name}")
    print(f"Results      : {len(results)}\n")

    for i, r in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(f"Product : {r.get('product_name')}")
        print(f"Source  : {r.get('source_file')}")
        print(f"Text    : {r.get('text')}\n")

if __name__ == "__main__":
    main()
