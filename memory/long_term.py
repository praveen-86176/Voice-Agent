from typing import Dict, List, Optional

from tools.memory_manager import MemoryManager


class LongTermMemory:
    def __init__(self):
        self.manager = MemoryManager()

    def save(self, text: str, memory_type: str) -> Dict:
        return self.manager.save_memory(memory_text=text, memory_type=memory_type)

    def recall(self, query: Optional[str] = None, limit: int = 5) -> List[Dict]:
        return self.manager.recall_memory(query=query, limit=limit)
