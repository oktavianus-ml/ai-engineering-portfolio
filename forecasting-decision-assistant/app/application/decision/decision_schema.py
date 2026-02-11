from typing import List, Dict

class DecisionResult(dict):
    """
    Standard output untuk Decision Assistant
    """
    action: str
    urgency: str
    risk: Dict[str, float]
    reasons: List[str]
    confidence: float
