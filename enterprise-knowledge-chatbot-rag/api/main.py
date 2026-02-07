# api/main.py
import json
import os
import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.chat_engine import handle_chat_engine
from api.ollama import MODEL


# =========================
# APP INIT
# =========================
app = FastAPI(title="MCNI AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# PATH
# =========================
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data/json"
PRODUCT_FILE = DATA_DIR / "products.json"
LOG_FILE = DATA_DIR / "logs" / "user_queries.jsonl"

# =========================
# LOAD PRODUCTS
# =========================
with open(PRODUCT_FILE, encoding="utf-8") as f:
    PRODUCTS = json.load(f)

# =========================
# SCHEMA
# =========================
class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"
    platform: Optional[str] = None


# =========================
# LOGGING
# =========================
def log_interaction(req, answer, products):
    os.makedirs(LOG_FILE.parent, exist_ok=True)

    log = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "user_id": req.user_id,
        "platform": req.platform,
        "question": req.message,
        "answer": answer,
        "products": [p.get("kode") for p in products] if products else []
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")


# =========================
# ENDPOINT
# =========================
@app.post("/chat")
def chat(req: ChatRequest):
    print("🔥 /chat HIT | MODEL:", MODEL)

    answer, products = handle_chat_engine(
        message=req.message,
        user_id=req.user_id,
        platform=req.platform,
        products_data=PRODUCTS
    )

    log_interaction(req, answer, products)

    return {
        "answer": answer,
        "products": products
    }


@app.get("/")
def health():
    return {"status": "ok"}
