# api/general_engine.py
from rag.call_llm import call_llm


def handle_general_flow(query: str) -> str | None:
    """
    Untuk pertanyaan definisi / umum
    yang tidak masuk product, sop, profile.
    """

    messages = [
        {
            "role": "system",
            "content": (
                "Anda adalah asisten CNI Indonesia.\n"
                "Jawab pertanyaan secara singkat dan jelas.\n"
                "Jika pertanyaan menyangkut data resmi perusahaan "
                "(tahun berdiri, visi misi, legal), "
                "jawab bahwa informasi resmi tersedia "
                "di dokumen perusahaan."
            )
        },
        {
            "role": "user",
            "content": query
        }
    ]

    return call_llm(messages, temperature=0.2)
