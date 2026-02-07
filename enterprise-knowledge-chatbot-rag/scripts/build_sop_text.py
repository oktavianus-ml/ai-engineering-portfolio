import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from api.loaders.pdf_loader import load_pdf

INPUT_PDF = "data/raw/pdf/sop_cs_cni.pdf"
OUTPUT_TXT = "data/processed/sop_text.txt"

os.makedirs("data/processed", exist_ok=True)

text = load_pdf(INPUT_PDF)

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write(text)

print("✅ sop_text.txt berhasil dibuat")
