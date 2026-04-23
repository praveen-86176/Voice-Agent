import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent.function_router import FunctionRouter
from agent.llm_provider import call_llm_with_tools
from agent.tool_schemas import TOOL_SCHEMAS


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)


class AriAgent:
    def __init__(self):
        self.router = FunctionRouter()
        self.session_context: List[Dict[str, str]] = []
        self.pending_action: Optional[Dict[str, Any]] = None

    def recall_top_memories(self, user_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.router.recall_memory(query=user_text, memory_type="all", limit=top_k)

    def format_memory_injection(self, memories: List[Dict[str, Any]]) -> str:
        if not memories:
            return "\n[MEMORY CONTEXT]: none"
        lines = [f"- ({m['memory_type']}/{m['importance']}) {m['content']}" for m in memories]
        return "\n[MEMORY CONTEXT]:\n" + "\n".join(lines)

    def build_messages(self, system_prompt: str, memory_context: str, user_text: str) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt + memory_context},
            *self.session_context,
            {"role": "user", "content": user_text},
        ]

    def call_llm(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        if tools:
            cloud_content, cloud_tool_calls = call_llm_with_tools(messages, TOOL_SCHEMAS)
            if cloud_tool_calls:
                return LLMResponse(
                    content=cloud_content,
                    tool_calls=[
                        ToolCall(name=tc["name"], arguments=tc["arguments"]) for tc in cloud_tool_calls
                    ],
                )
            if cloud_content:
                return LLMResponse(content=cloud_content)
            # Local fallback planner so the loop works even without a cloud LLM.
            return self._plan_tool_call(messages[-1]["content"])
        return self._render_final_reply(messages)

    def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[Dict[str, str]]:
        tool_messages: List[Dict[str, str]] = []
        for tool_call in tool_calls:
            result = self.router.route(tool_call.name, tool_call.arguments)
            tool_messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(
                        {
                            "tool_name": tool_call.name,
                            "arguments": tool_call.arguments,
                            "result": result,
                        }
                    ),
                }
            )
        return tool_messages

    def update_session_context(self, user_text: str, final_response: str) -> None:
        self.session_context.append({"role": "user", "content": user_text})
        self.session_context.append({"role": "assistant", "content": final_response})
        self.session_context = self.session_context[-10:]

    def _plan_tool_call(self, text: str) -> LLMResponse:
        raw = text.strip()
        lowered = raw.lower()

        if not raw:
            return LLMResponse(content="I didn't quite catch that — could you repeat it?")

        if self.pending_action:
            follow_up = self._handle_pending_action(raw)
            if follow_up:
                return follow_up

        if lowered in {"hi", "hello", "hey", "good morning", "good evening"}:
            return LLMResponse(content="Hey, I’m here. Want me to manage a task or remember something important?")

        if any(p in lowered for p in ["what's on my list", "show tasks", "list tasks", "what do i have"]):
            args: Dict[str, Any] = {"status": "all", "priority": "all", "due_today": "today" in lowered}
            return LLMResponse(tool_calls=[ToolCall(name="list_todos", arguments=args)])

        if any(p in lowered for p in ["mark", "complete", "done", "update task", "change "]):
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="update_todo",
                        arguments={
                            "task_name": self._extract_task_title(raw),
                            "status": "done",
                        },
                    )
                ]
            )

        if any(p in lowered for p in ["delete", "remove", "cancel task"]):
            if "yes" not in lowered and "confirm" not in lowered:
                task_name = self._extract_task_title(raw)
                self.pending_action = {
                    "type": "confirm_delete_todo",
                    "arguments": {"task_name": task_name, "confirmed": True},
                }
                return LLMResponse(content=f"Do you want me to delete {task_name}?")
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="delete_todo",
                        arguments={
                            "task_name": self._extract_task_title(raw),
                            "confirmed": True,
                        },
                    )
                ]
            )

        if any(p in lowered for p in ["do you remember", "what did i tell you", "recall", "upcoming events"]):
            recall_query = self._extract_query(raw) or raw
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="recall_memory",
                        arguments={"query": recall_query, "memory_type": "all", "limit": 3},
                    )
                ]
            )

        if self._looks_like_memory_statement(lowered):
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="save_memory",
                        arguments={
                            "content": raw,
                            "memory_type": self._classify_memory_type(raw),
                            "importance": self._extract_importance(raw),
                        },
                    )
                ]
            )

        if any(p in lowered for p in ["add ", "remind me to", "i need to"]):
            title = self._extract_task_title(raw)
            if not title:
                return LLMResponse(content="What should I add to your list?")
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        name="add_todo",
                        arguments={
                            "title": title,
                            "due_date": self._extract_due_date(raw),
                            "priority": self._extract_priority(raw),
                        },
                    )
                ]
            )

        if self._looks_like_task_statement(raw):
            self.pending_action = {
                "type": "confirm_add_todo",
                "arguments": {
                    "title": raw,
                    "priority": self._extract_priority(raw),
                    "due_date": self._extract_due_date(raw),
                },
            }
            return LLMResponse(content=f"Do you want me to add {raw} to your to-do list?")

        return LLMResponse(
            content="I’m here and ready. Should I add a task, update one, or save something important to remember?"
        )

    def _handle_pending_action(self, text: str) -> Optional[LLMResponse]:
        lowered = text.lower().strip()
        action = self.pending_action or {}
        yes_words = {"yes", "yeah", "yep", "sure", "ok", "okay", "do it"}
        no_words = {"no", "nope", "nah", "cancel", "stop"}

        if lowered in yes_words and action.get("type") == "confirm_add_todo":
            args = action.get("arguments", {})
            self.pending_action = None
            return LLMResponse(tool_calls=[ToolCall(name="add_todo", arguments=args)])

        if lowered in yes_words and action.get("type") == "confirm_delete_todo":
            args = action.get("arguments", {})
            self.pending_action = None
            return LLMResponse(tool_calls=[ToolCall(name="delete_todo", arguments=args)])

        if lowered in no_words:
            self.pending_action = None
            return LLMResponse(content="No problem. Tell me what you want to do next.")

        # Keep waiting for explicit confirmation if user gave unrelated text.
        if action.get("type") == "confirm_add_todo":
            title = action.get("arguments", {}).get("title", "that")
            return LLMResponse(content=f"Just to confirm, should I add {title} to your list?")
        if action.get("type") == "confirm_delete_todo":
            title = action.get("arguments", {}).get("task_name", "that task")
            return LLMResponse(content=f"Just to confirm, should I delete {title}?")
        return None

    def _looks_like_task_statement(self, text: str) -> bool:
        lowered = text.lower().strip()
        if len(lowered) < 3:
            return False
        if lowered in {"yes", "no"}:
            return False
        # Basic heuristic: short imperative-like phrases are likely tasks.
        return len(lowered.split()) <= 8

    def _looks_like_memory_statement(self, lowered: str) -> bool:
        triggers = [
            "remember that",
            "my anniversary",
            "my birthday",
            "i prefer",
            "i got promoted",
            "important that",
            "i usually",
            "i like",
        ]
        return any(t in lowered for t in triggers)

    def _render_final_reply(self, messages: List[Dict[str, str]]) -> LLMResponse:
        tool_msg = next((m for m in reversed(messages) if m["role"] == "tool"), None)
        if not tool_msg:
            return LLMResponse(content="I’m ready when you are.")

        payload = json.loads(tool_msg["content"])
        tool_name = payload.get("tool_name")
        result = payload.get("result")

        if tool_name == "add_todo":
            return LLMResponse(content=f"Done! I added {result['title']} to your list.")
        if tool_name == "update_todo":
            if not result:
                return LLMResponse(content="I couldn't find that task — could you describe it differently?")
            return LLMResponse(content=f"Done. I updated {result['title']}.")
        if tool_name == "delete_todo":
            if not result:
                return LLMResponse(content="I couldn't find that task — could you describe it differently?")
            return LLMResponse(content="Done. I removed that task from your list.")
        if tool_name == "list_todos":
            if not result:
                return LLMResponse(content="You have no tasks right now.")
            titles = [t["title"] for t in result[:5]]
            if len(titles) == 1:
                return LLMResponse(content=f"You have one task: {titles[0]}.")
            return LLMResponse(content=f"You have {len(titles)} tasks: {', '.join(titles[:-1])}, and {titles[-1]}.")
        if tool_name == "save_memory":
            return LLMResponse(content="Got it. I’ll remember that.")
        if tool_name == "recall_memory":
            if not result:
                return LLMResponse(content="I don’t have anything relevant saved yet.")
            return LLMResponse(content=f"I remember you mentioned {result[0]['content']}.")
        return LLMResponse(content="Done.")

    def _extract_priority(self, text: str) -> str:
        lowered = text.lower()
        if "high priority" in lowered or "urgent" in lowered:
            return "high"
        if "low priority" in lowered:
            return "low"
        return "medium"

    def _extract_due_date(self, text: str) -> Optional[str]:
        match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
        return match.group(1) if match else None

    def _extract_task_title(self, text: str) -> str:
        lowered = text.lower()
        patterns: List[str] = [
            r"add\s+(.+)",
            r"remind me to\s+(.+)",
            r"i need to\s+(.+)",
            r"mark\s+(.+?)\s+as\s+(?:done|complete)",
            r"delete\s+(.+)",
            r"remove\s+(.+)",
            r"change\s+(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, lowered, flags=re.IGNORECASE)
            if match:
                extracted = text[match.start(1) : match.end(1)].strip(" .")
                extracted = re.sub(
                    r"\b(yes|confirm|please|as done|as complete)\b.*$",
                    "",
                    extracted,
                    flags=re.IGNORECASE,
                ).strip(" ,.")
                return extracted
        return text.strip(" .")

    def _extract_query(self, text: str) -> Optional[str]:
        cleaned = re.sub(
            r"do you remember|what did i tell you|recall|any upcoming events",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        return cleaned or None

    def _classify_memory_type(self, text: str) -> str:
        lowered = text.lower()
        if "prefer" in lowered:
            return "preference"
        if any(word in lowered for word in ["promoted", "graduated", "won", "achieved"]):
            return "milestone"
        if any(word in lowered for word in ["birthday", "anniversary", "appointment"]):
            return "event"
        return "general"

    def _extract_importance(self, text: str) -> str:
        lowered = text.lower()
        if "very important" in lowered or "critical" in lowered:
            return "high"
        if "not important" in lowered:
            return "low"
        return "medium"
