from pathlib import Path

# ==================================================
# BASE PROJECT PATH
# ==================================================
BASE_DIR = Path(__file__).resolve().parent

# ==================================================
# DATA ROOT
# ==================================================
DATA_DIR = BASE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DATA_RAW_PDF_DIR = DATA_DIR / "raw" / "pdf"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
LOG_DIR = DATA_DIR / "logs"

# ==================================================
# RAW DATA FILES
# ==================================================
PRODUCT_JSON = DATA_DIR / "json" / "products.json"

# ==================================================
# VECTOR STORE PATHS
# ==================================================
SOP_VECTOR_DIR = VECTORSTORE_DIR / "sop"
PRODUCT_VECTOR_DIR = VECTORSTORE_DIR / "products"
PROFILE_VECTOR_DIR = VECTORSTORE_DIR / "profile"

# ==================================================
# LOG & MEMORY FILES
# ==================================================
CHAT_LOG_FILE = LOG_DIR / "chat_logs.jsonl"
PENDING_FILE = LOG_DIR / "pending_questions.json"
LEARNED_FILE = LOG_DIR / "learned_answers.json"

# ==================================================
# LLM CONFIG
# ==================================================
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma3:4b"
EMBED_MODEL = "nomic-embed-text"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
