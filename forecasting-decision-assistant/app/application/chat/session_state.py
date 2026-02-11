# app/application/chat/session_state.py
import time


class SessionState:
    """
    Simple in-memory session state
    """

    def __init__(self, ttl_seconds: int = 120):
        self.ttl = ttl_seconds
        self._store = {}

    def set(self, key: str, value: dict):
        self._store[key] = {
            "value": value,
            "ts": time.time(),
        }

    def get(self, key: str):
        item = self._store.get(key)
        if not item:
            return None

        if time.time() - item["ts"] > self.ttl:
            self._store.pop(key, None)
            return None

        return item["value"]

    def pop(self, key: str):
        item = self._store.pop(key, None)
        if not item:
            return None
        return item["value"]

    def clear(self):
        self._store.clear()


# ✅ SINGLETON GLOBAL
session_state = SessionState(ttl_seconds=120)