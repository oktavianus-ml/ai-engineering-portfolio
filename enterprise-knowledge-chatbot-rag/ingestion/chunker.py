from typing import List, Dict
import re


# =========================
# UTIL: split paragraf
# =========================
def split_paragraphs(text: str) -> list[str]:
    """
    Split SOP PDF text menjadi paragraf bermakna.
    """
    # normalisasi bullet
    text = text.replace("•", "\n• ")

    # paksa newline sebelum heading bernomor (meski di tengah kalimat)
    text = re.sub(r"(\.)\s*(\d+\.\s+[A-Z])", r"\1\n\2", text)

    # split berdasarkan heading bernomor
    parts = re.split(r"\n(?=\d+\.\s+[A-Z])", text)

    final = []

    for p in parts:
        p = p.strip()
        if not p:
            continue

        # split heading kapital
        subs = re.split(r"\n(?=[A-Z][A-Z\s]{5,})", p)

        for s in subs:
            s = s.strip()
            if len(s) > 80:
                final.append(s)

    return final


# =========================
# UTIL: deteksi section SOP
# =========================
def detect_section(text: str) -> str:
    """
    Deteksi section SOP dengan mengambil heading PALING RELEVAN
    (muncul terakhir di dalam chunk).
    """
    section = "UMUM"

    for line in text.splitlines():
        l = line.strip().upper()

        if not l:
            continue

        if "PROFIL PERUSAHAAN" in l:
            section = "PROFIL PERUSAHAAN"
        elif "VISI DAN MISI" in l:
            section = "VISI DAN MISI"
        elif "DASAR DAN LANDASAN" in l:
            section = "DASAR DAN LANDASAN HUKUM"
        elif "TUJUAN SOP" in l:
            section = "TUJUAN SOP"
        elif "RUANG LINGKUP" in l:
            section = "RUANG LINGKUP"
        elif "TANGGUNG JAWAB" in l:
            section = "TANGGUNG JAWAB DAN WEWENANG"
        elif "ALUR PELAYANAN" in l:
            section = "ALUR PELAYANAN CUSTOMER SERVICE"
        elif "PENANGANAN KELUHAN" in l:
            section = "PENANGANAN KELUHAN DAN KOMPLAIN"

    return section




# =========================
# CHUNKER PDF (SOP)
# =========================
def chunk_pdf_page(
    text: str,
    source: str,
    page: int,
    chunk_size: int = 400,
    overlap: int = 80
) -> List[Dict]:
    """
    Chunk satu halaman PDF SOP menjadi beberapa chunk bermakna.
    """
    chunks = []
    section = detect_section(text)
    buffer = ""

    for para in split_paragraphs(text):
        if len(buffer) + len(para) <= chunk_size:
            buffer += " " + para
        else:
            chunks.append({
                "text": buffer.strip(),
                "source": source,
                "page": page,
                "section": section,
                "type": "pdf"
            })
            buffer = buffer[-overlap:] + " " + para

    if buffer.strip():
        chunks.append({
            "text": buffer.strip(),
            "source": source,
            "page": page,
            "section": section,
            "type": "pdf"
        })

    return chunks


# =========================
# CHUNKER GENERIC (WEB / TEXT)
# =========================
def chunk_text(
    text: str,
    source: str,
    doc_type: str = "text",
    chunk_size: int = 500,
    overlap: int = 80
) -> List[Dict]:
    """
    Chunker generic (web, artikel, catatan).
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append({
                "text": chunk,
                "source": source,
                "type": doc_type
            })

        start = end - overlap

    return chunks
