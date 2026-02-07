from core.composer import (
    detect_intent,
    compose_sop_answer,
    compose_profile_answer,
    compose_general_answer
)

# =========================
# TEST INTENT DETECTION
# =========================
def test_detect_intent():
    tests = {
        "Saya mau komplain layanan": "complaint",
        "Apa visi dan misi perusahaan?": "vision",
        "Profil perusahaan CNI": "profile",
        "Halo": "general"
    }

    for query, expected in tests.items():
        result = detect_intent(query)
        print(f"[INTENT] {query} → {result}")
        assert result == expected


# =========================
# TEST SOP COMPOSER
# =========================
def test_compose_sop_answer():
    dummy_chunks = [
        {
            "function": "complaint",
            "text": "Keluhan pelanggan ditangani oleh customer service melalui alur eskalasi."
        },
        {
            "function": "complaint",
            "text": "Setiap komplain harus dicatat dan ditindaklanjuti."
        }
    ]

    answer = compose_sop_answer(
        query="Bagaimana prosedur keluhan?",
        sop_chunks=dummy_chunks
    )

    print("\n[SOP ANSWER]")
    print(answer)

    assert "keluhan" in answer.lower()


# =========================
# TEST PROFILE COMPOSER
# =========================
def test_compose_profile_answer():
    dummy_chunks = [
        {"text": "PT CNI merupakan perusahaan yang bergerak di bidang produk kesehatan."},
        {"text": "CNI berkomitmen meningkatkan kualitas hidup masyarakat."}
    ]

    answer = compose_profile_answer(
        query="Profil perusahaan",
        chunks=dummy_chunks
    )

    print("\n[PROFILE ANSWER]")
    print(answer)

    assert "perusahaan" in answer.lower()


# =========================
# TEST GENERAL COMPOSER
# =========================
def test_compose_general_answer():
    answer = compose_general_answer("Halo")

    print("\n[GENERAL ANSWER]")
    print(answer)

    assert "maaf" in answer.lower()


if __name__ == "__main__":
    test_detect_intent()
    test_compose_sop_answer()
    test_compose_profile_answer()
    test_compose_general_answer()

    print("\n✅ BASIC COMPOSER TEST PASSED")
