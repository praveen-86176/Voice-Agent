import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import TODOS_DB_PATH


class TodoManager:
    def __init__(self, db_path: Path = TODOS_DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    due_date TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add_todo(
        self, title: str, due_date: Optional[str] = None, priority: str = "medium"
    ) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        priority = priority.lower() if priority else "medium"
        if priority not in {"low", "medium", "high"}:
            priority = "medium"
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO todos(title, due_date, priority, status, created_at, updated_at)
                VALUES(?, ?, ?, 'pending', ?, ?)
                """,
                (title.strip(), due_date, priority.lower(), now, now),
            )
            conn.commit()
            todo_id = cursor.lastrowid
        return self.get_todo(todo_id)

    def get_todo(self, todo_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
            return dict(row) if row else None

    def list_todos(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        due_today: bool = False,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM todos WHERE 1=1"
        params: List[Any] = []

        if status and status != "all":
            query += " AND status = ?"
            params.append(status)
        if priority and priority != "all":
            query += " AND priority = ?"
            params.append(priority)
        if due_date:
            query += " AND due_date = ?"
            params.append(due_date)
        if due_today:
            query += " AND due_date = ?"
            params.append(date.today().isoformat())

        query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def update_todo(
        self,
        task_id: Optional[int] = None,
        task_name: Optional[str] = None,
        new_title: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        target = self._resolve_todo(task_id, task_name)
        if not target:
            return None

        fields = []
        values: List[Any] = []
        if new_title is not None:
            fields.append("title = ?")
            values.append(new_title.strip())
        if due_date is not None:
            fields.append("due_date = ?")
            values.append(due_date)
        if priority is not None:
            fields.append("priority = ?")
            values.append(priority.lower())
        if status is not None:
            normalized_status = status.lower()
            if normalized_status not in {"pending", "in_progress", "done"}:
                normalized_status = "pending"
            fields.append("status = ?")
            values.append(normalized_status)

        if not fields:
            return target

        fields.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(target["id"])

        with self._connect() as conn:
            conn.execute(f"UPDATE todos SET {', '.join(fields)} WHERE id = ?", values)
            conn.commit()
        return self.get_todo(target["id"])

    def delete_todo(
        self, task_id: Optional[int] = None, task_name: Optional[str] = None
    ) -> bool:
        target = self._resolve_todo(task_id, task_name)
        if not target:
            return False
        with self._connect() as conn:
            conn.execute("DELETE FROM todos WHERE id = ?", (target["id"],))
            conn.commit()
        return True

    def _resolve_todo(
        self, task_id: Optional[int], task_name: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        if task_id is not None:
            return self.get_todo(task_id)
        if task_name:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM todos WHERE title LIKE ? ORDER BY created_at DESC LIMIT 1",
                    (f"%{task_name}%",),
                ).fetchone()
                return dict(row) if row else None
        return None
