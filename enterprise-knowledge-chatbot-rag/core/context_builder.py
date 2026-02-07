# core/context_builder.py

class ContextBuilder:
    """
    Build context string from retrieved documents for RAG
    """

    def build(self, docs) -> str:
        contexts = []

        for doc in docs:
            if hasattr(doc, "page_content"):
                text = doc.page_content
            elif isinstance(doc, dict):
                text = (
                    doc.get("content")
                    or doc.get("text")
                    or doc.get("deskripsi")
                    or ""
                )
            else:
                text = str(doc)

            if text and text.strip():
                contexts.append(text.strip())

        return "\n\n".join(contexts)
