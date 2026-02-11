import re

class HorizonParser:
    def parse(self, text: str) -> int:
        match = re.search(r"(\d+)\s*(hari|day|days)", text.lower())
        if match:
            return int(match.group(1))
        return 30  # default
