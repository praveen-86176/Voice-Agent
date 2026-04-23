import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.agent_core import AriAgent
from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_schemas import TOOL_SCHEMAS


BASE_DIR = Path(__file__).resolve().parent
UI_PATH = BASE_DIR / "web" / "index.html"
agent = AriAgent()


def process_message(user_text: str) -> str:
    relevant_memories = agent.recall_top_memories(user_text, top_k=3)
    memory_context = agent.format_memory_injection(relevant_memories)
    messages = agent.build_messages(
        system_prompt=SYSTEM_PROMPT,
        memory_context=memory_context,
        user_text=user_text,
    )
    response = agent.call_llm(messages, tools=TOOL_SCHEMAS)
    if response.tool_calls:
        tool_messages = agent.execute_tool_calls(response.tool_calls)
        messages.extend(tool_messages)
        final_response = agent.call_llm(messages).content
    else:
        final_response = response.content
    agent.update_session_context(user_text, final_response)
    return final_response


class AriaHandler(BaseHTTPRequestHandler):
    def _read_json_body(self) -> Optional[Dict[str, Any]]:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(body) if body else {}
        except json.JSONDecodeError:
            return None

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, content: str, status: int = 200) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._send_html(UI_PATH.read_text(encoding="utf-8"))
            return
        if self.path.startswith("/api/todos"):
            todos = agent.router.list_todos(status="all", priority="all", due_today=False)
            self._send_json({"todos": todos})
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        if self.path == "/chat":
            payload = self._read_json_body()
            if payload is None:
                self._send_json({"error": "Invalid JSON body"}, status=400)
                return

            user_text = str(payload.get("message", "")).strip()
            if not user_text:
                self._send_json({"reply": "I didn't quite catch that — could you repeat it?"})
                return

            reply = process_message(user_text)
            self._send_json({"reply": reply})
            return

        if self.path == "/api/todos/update":
            payload = self._read_json_body()
            if payload is None:
                self._send_json({"error": "Invalid JSON body"}, status=400)
                return
            updated = agent.router.update_todo(
                task_id=payload.get("task_id"),
                task_name=payload.get("task_name"),
                status=payload.get("status"),
                new_title=payload.get("new_title"),
                due_date=payload.get("due_date"),
                priority=payload.get("priority"),
            )
            self._send_json({"todo": updated})
            return

        if self.path == "/api/todos/delete":
            payload = self._read_json_body()
            if payload is None:
                self._send_json({"error": "Invalid JSON body"}, status=400)
                return
            ok = agent.router.delete_todo(
                task_id=payload.get("task_id"),
                task_name=payload.get("task_name"),
                confirmed=True,
            )
            self._send_json({"deleted": ok})
            return

        if self.path == "/api/todos/add":
            payload = self._read_json_body()
            if payload is None:
                self._send_json({"error": "Invalid JSON body"}, status=400)
                return
            title = str(payload.get("title", "")).strip()
            if not title:
                self._send_json({"error": "title required"}, status=400)
                return
            todo = agent.router.add_todo(
                title=title,
                due_date=payload.get("due_date"),
                priority=payload.get("priority", "medium"),
            )
            self._send_json({"todo": todo})
            return

        if self.path != "/chat":
            self._send_json({"error": "Not found"}, status=404)
            return

    def log_message(self, format: str, *args: List[Any]) -> None:  # noqa: A003
        return


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), AriaHandler)
    print(f"ARIA web running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
