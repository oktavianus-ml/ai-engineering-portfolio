import json, os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_FILE = os.path.join(BASE_DIR, "data/chat_logs.jsonl")

def save_log(question, products, answer):
    log = {
        "time": datetime.now().isoformat(),
        "question": question,
        "products": [p["kode"] for p in products],
        "answer": answer
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")
