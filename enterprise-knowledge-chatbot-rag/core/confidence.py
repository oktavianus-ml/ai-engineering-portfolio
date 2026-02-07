from datetime import datetime
import json
from pathlib import Path


# =========================
# CONFIDENCE LOGGING
# =========================

# Resolve project root safely
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# logs/ di dalam project
CONF_LOG = PROJECT_ROOT / "logs" / "confidence_log.jsonl"

# Pastikan folder ada
CONF_LOG.parent.mkdir(parents=True, exist_ok=True)



def log_confidence_event(
    *,
    query: str,
    score: float,
    label: str,
    domain: str = "product"
):
    """
    Log confidence decision for audit & analytics.

    Parameters:
    - query  : original user question
    - score  : top cosine similarity score
    - label  : confidence label (tinggi / sedang / rendah)
    - domain : domain router (default: product)

    Format:
    One JSON object per line (JSONL), append-only.
    """

    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "score": round(score, 3),
        "label": label,
        "domain": domain
    }

    with open(CONF_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
