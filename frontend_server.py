import os
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.agent_core import AriAgent
from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_schemas import TOOL_SCHEMAS
from agent.function_router import FunctionRouter

app = FastAPI(title="ARIA Voice Agent API")
agent = AriAgent()
router = FunctionRouter()

# Serve static files from the web directory
# Since we only have index.html, we can just serve it manually at root
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("web/index.html", "r") as f:
        return f.read()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_text = request.message
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Inject Long-Term Memory Context
    relevant_memories = agent.recall_top_memories(user_text, top_k=3)
    memory_context = agent.format_memory_injection(relevant_memories)

    # Build Message Payload
    messages = agent.build_messages(
        system_prompt=SYSTEM_PROMPT,
        memory_context=memory_context,
        user_text=user_text,
    )

    # LLM Reasoning (with tool schema)
    response = agent.call_llm(messages, tools=TOOL_SCHEMAS)

    # Tool Execution or Direct Reply
    if response.tool_calls:
        tool_messages = agent.execute_tool_calls(response.tool_calls)
        messages.extend(tool_messages)
        # Note: In a real app, we might loop here if there are multiple tool steps
        final_response = agent.call_llm(messages).content
    else:
        final_response = response.content

    # Update Session Context
    agent.update_session_context(user_text, final_response)
    
    return ChatResponse(reply=final_response)

@app.get("/api/todos")
async def get_todos():
    todos = router.list_todos()
    return {"todos": todos}

class AddTodoRequest(BaseModel):
    title: str
    due_date: Optional[str] = None
    priority: Optional[str] = "medium"

@app.post("/api/todos/add")
async def add_todo(request: AddTodoRequest):
    todo = router.add_todo(
        title=request.title, 
        due_date=request.due_date, 
        priority=request.priority
    )
    return todo

class UpdateTodoRequest(BaseModel):
    task_id: int
    status: str

@app.post("/api/todos/update")
async def update_todo(request: UpdateTodoRequest):
    todo = router.update_todo(
        task_id=request.task_id, 
        status=request.status
    )
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

class DeleteTodoRequest(BaseModel):
    task_id: int

@app.post("/api/todos/delete")
async def delete_todo(request: DeleteTodoRequest):
    success = router.delete_todo(task_id=request.task_id, confirmed=True)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
