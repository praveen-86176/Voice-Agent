from collections import deque
from typing import Deque, Dict, List


class ShortTermMemory:
    def __init__(self, max_turns: int = 12):
        self.max_turns = max_turns
        self.turns: Deque[Dict[str, str]] = deque(maxlen=max_turns)

    def add_turn(self, role: str, text: str) -> None:
        self.turns.append({"role": role, "text": text})

    def get_context(self) -> List[Dict[str, str]]:
        return list(self.turns)
