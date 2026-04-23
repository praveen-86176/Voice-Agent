from typing import Any, Dict, Optional

from tools.memory_manager import MemoryManager
from tools.todo_manager import TodoManager


class FunctionRouter:
    def __init__(self):
        self.todo_manager = TodoManager()
        self.memory_manager = MemoryManager()

    def add_todo(
        self, title: str, due_date: Optional[str] = None, priority: str = "medium"
    ) -> Dict[str, Any]:
        return self.todo_manager.add_todo(title=title, due_date=due_date, priority=priority)

    def update_todo(
        self,
        task_id: Optional[int] = None,
        task_name: Optional[str] = None,
        new_title: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        return self.todo_manager.update_todo(
            task_id=task_id,
            task_name=task_name,
            new_title=new_title,
            due_date=due_date,
            priority=priority,
            status=status,
        )

    def delete_todo(
        self,
        task_id: Optional[int] = None,
        task_name: Optional[str] = None,
        confirmed: bool = False,
    ) -> bool:
        if not confirmed:
            return False
        return self.todo_manager.delete_todo(task_id=task_id, task_name=task_name)

    def list_todos(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_today: bool = False,
    ):
        return self.todo_manager.list_todos(
            status=status,
            priority=priority,
            due_today=due_today,
        )

    def save_memory(
        self, content: str, memory_type: str, importance: str = "medium"
    ) -> Dict[str, Any]:
        return self.memory_manager.save_memory(
            content=content, memory_type=memory_type, importance=importance
        )

    def recall_memory(
        self, query: str, memory_type: str = "all", limit: int = 5
    ) -> Dict[str, Any]:
        return self.memory_manager.recall_memory(
            query=query,
            memory_type=memory_type,
            limit=limit,
        )

    def route(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        handlers = {
            "add_todo": self.add_todo,
            "update_todo": self.update_todo,
            "delete_todo": self.delete_todo,
            "list_todos": self.list_todos,
            "save_memory": self.save_memory,
            "recall_memory": self.recall_memory,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        return handler(**arguments)
