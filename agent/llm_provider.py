import json
from typing import Any, Dict, List, Tuple

from config import GROQ_API_KEY, GROQ_MODEL, LLM_PROVIDER


def _to_openai_tools(tool_schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tools: List[Dict[str, Any]] = []
    for schema in tool_schemas:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema.get("description", ""),
                    "parameters": schema.get("parameters", {"type": "object", "properties": {}}),
                },
            }
        )
    return tools


def call_llm_with_tools(
    messages: List[Dict[str, str]],
    tool_schemas: List[Dict[str, Any]],
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns (assistant_content, tool_calls).
    tool_calls format: [{"name": "...", "arguments": {...}}]
    """
    if LLM_PROVIDER != "groq" or not GROQ_API_KEY:
        return "", []

    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=_to_openai_tools(tool_schemas),
            tool_choice="auto",
            temperature=0.2,
        )
        msg = response.choices[0].message
        calls: List[Dict[str, Any]] = []
        for tc in msg.tool_calls or []:
            args = tc.function.arguments or "{}"
            parsed = json.loads(args) if isinstance(args, str) else args
            calls.append({"name": tc.function.name, "arguments": parsed})
        return (msg.content or "", calls)
    except Exception:
        return "", []
