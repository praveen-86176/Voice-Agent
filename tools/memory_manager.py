import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import MEMORIES_DB_PATH
from tools.vector_memory import VectorMemoryIndex


VALID_MEMORY_TYPES = {"event", "preference", "milestone", "general"}
VALID_IMPORTANCE = {"low", "medium", "high"}


class MemoryManager:
    def __init__(self, db_path: Path = MEMORIES_DB_PATH):
        self.db_path = str(db_path)
        self.vector_index = VectorMemoryIndex()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    importance TEXT NOT NULL DEFAULT 'medium',
                    timestamp TEXT NOT NULL,
                    embedding TEXT
                )
                """
            )
            conn.commit()

    def save_memory(
        self,
        content: str,
        memory_type: str,
        importance: str = "medium",
        embedding: Optional[str] = None,
    ) -> Dict[str, Any]:
        memory_type = memory_type.lower()
        if memory_type not in VALID_MEMORY_TYPES:
            memory_type = "general"
        importance = importance.lower()
        if importance not in VALID_IMPORTANCE:
            importance = "medium"
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO memories(content, memory_type, importance, timestamp, embedding)
                VALUES (?, ?, ?, ?, ?)
                """,
                (content.strip(), memory_type, importance, now, embedding),
            )
            conn.commit()
            memory_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            saved = dict(row)

        self.vector_index.add_memory(
            memory_id=memory_id,
            content=saved["content"],
            metadata={
                "memory_type": saved["memory_type"],
                "importance": saved["importance"],
                "timestamp": saved["timestamp"],
            },
        )
        return saved

    def recall_memory(
        self,
        query: str,
        memory_type: str = "all",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        normalized_type = memory_type.lower() if memory_type else "all"
        with self._connect() as conn:
            vector_ids = self.vector_index.search(
                query=query,
                limit=limit,
                memory_type=normalized_type,
            )
            if vector_ids:
                placeholders = ",".join("?" for _ in vector_ids)
                order_case = " ".join(
                    [f"WHEN {memory_id} THEN {rank}" for rank, memory_id in enumerate(vector_ids)]
                )
                rows = conn.execute(
                    f"""
                    SELECT * FROM memories
                    WHERE id IN ({placeholders})
                    ORDER BY CASE id {order_case} END
                    LIMIT ?
                    """,
                    [*vector_ids, limit],
                ).fetchall()
                if rows:
                    return [dict(r) for r in rows]

            query_sql = "SELECT * FROM memories WHERE content LIKE ?"
            params: List[Any] = [f"%{query}%"]
            if normalized_type != "all":
                query_sql += " AND memory_type = ?"
                params.append(normalized_type)
            query_sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query_sql, params).fetchall()
            return [dict(r) for r in rows]
