import json
import os
from datetime import datetime
import re

# ======================
# PATH
# ======================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ENABLE_AUTO_LEARN = False

LEARNED_FILE = os.path.join(DATA_DIR, "learned_answers.json")
PENDING_FILE = os.path.join(DATA_DIR, "pending_questions.json")
CHAT_LOG_FILE = os.path.join(DATA_DIR, "chat_logs.jsonl")

# ======================
# FAILURE KEYWORDS
# ======================
FAIL_KEYWORDS = [
    "❌",
    "tidak ditemukan",
    "belum tersedia",
    "maaf",
]

# ======================
# UTIL
# ======================
def normalize(text: str) -> str:
    return (
        text.lower()
        .strip()
        .replace('"', "")
        .replace("?", "")
    )

def _ensure(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f)

def _load(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else []
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except json.JSONDecodeError:
        return []

def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================
# FAILURE DETECTOR
# ======================
def is_failed_answer(log: dict) -> bool:
    answer = log.get("answer", "").lower()
    products = log.get("products", [])

    if not products and any(k in answer for k in FAIL_KEYWORDS):
        return True

    return False

# ======================
# PUBLIC API
# ======================
def get_learned_answer(question: str, user_id=None):
    q = normalize(question)
    learned = _load(LEARNED_FILE)

    for item in learned:
        if normalize(item["question"]) == q:
            return item["answer"]

    return None

def save_pending(question: str, source="runtime"):
    pending = _load(PENDING_FILE)
    nq = normalize(question)

    if any(normalize(p["question"]) == nq for p in pending):
        return

    pending.append({
        "question": question,
        "source": source,
        "created_at": datetime.now().isoformat()
    })

    _save(PENDING_FILE, pending)

def save_learned(question: str, answer: str, related_products=None):

    if not ENABLE_AUTO_LEARN:
        return  # ⛔ STOP DI SINI

    if not question or not answer:
        return

    if related_products is None:
        related_products = []

    learned = _load(LEARNED_FILE)

    learned.append({
        "question": question,
        "answer": answer,
        "products": related_products,
        "created_at": datetime.now().isoformat()
    })

    _save(LEARNED_FILE, learned)

    # hapus dari pending
    pending = _load(PENDING_FILE)
    pending = [p for p in pending if p["question"] != question]
    _save(PENDING_FILE, pending)


def sync_failed_from_chat_logs():
    if not os.path.exists(CHAT_LOG_FILE):
        return 0

    pending = _load(PENDING_FILE)
    pending_norm = {normalize(p["question"]) for p in pending}
    added = 0

    with open(CHAT_LOG_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                log = json.loads(line)
            except json.JSONDecodeError:
                continue

            q = log.get("question", "").strip()
            if not q:
                continue

            if not is_failed_answer(log):
                continue

            nq = normalize(q)
            if nq in pending_norm:
                continue

            pending.append({
                "question": q,
                "source": "chat_logs",
                "created_at": log.get("time", datetime.now().isoformat())
            })
            pending_norm.add(nq)
            added += 1

    _save(PENDING_FILE, pending)
    return added

def normalize(text: str) -> str:
    if not text:
        return ""

    text = text.lower().strip()

    # hapus tanda baca
    text = re.sub(r"[^\w\s]", "", text)

    # rapikan spasi
    text = re.sub(r"\s+", " ", text)

    return text