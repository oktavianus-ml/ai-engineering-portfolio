from pypdf import PdfReader

def load_pdf(path: str):
    reader = PdfReader(path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()

        if len(text) < 30:
            continue

        pages.append({
            "page": i + 1,
            "text": text
        })

    return pages
