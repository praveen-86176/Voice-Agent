TOOL_SCHEMAS = [
    {
        "name": "add_todo",
        "description": "Add a new task to the user's to-do list",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task description"},
                "due_date": {
                    "type": "string",
                    "description": "Due date in YYYY-MM-DD format, optional",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "update_todo",
        "description": "Update an existing task by ID or name",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to update"},
                "task_name": {"type": "string", "description": "Name match if ID is unknown"},
                "new_title": {"type": "string", "description": "Updated task title"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "done"],
                },
                "due_date": {"type": "string", "description": "Updated due date"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": [],
        },
    },
    {
        "name": "delete_todo",
        "description": "Delete a task by ID or name",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task"},
                "task_name": {"type": "string", "description": "Name match if ID unknown"},
                "confirmed": {"type": "boolean", "description": "User has confirmed deletion"},
            },
            "required": ["confirmed"],
        },
    },
    {
        "name": "list_todos",
        "description": "Retrieve and list tasks based on filters",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "done", "all"],
                },
                "priority": {"type": "string", "enum": ["low", "medium", "high", "all"]},
                "due_today": {
                    "type": "boolean",
                    "description": "Only show tasks due today",
                },
            },
            "required": [],
        },
    },
    {
        "name": "save_memory",
        "description": "Store an important user event, preference, or milestone",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The memory content to store"},
                "memory_type": {
                    "type": "string",
                    "enum": ["event", "preference", "milestone", "general"],
                },
                "importance": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["content", "memory_type"],
        },
    },
    {
        "name": "recall_memory",
        "description": "Retrieve relevant past memories based on a query",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search memories for"},
                "memory_type": {
                    "type": "string",
                    "enum": ["event", "preference", "milestone", "general", "all"],
                },
                "limit": {"type": "integer", "description": "Max number of memories to return"},
            },
            "required": ["query"],
        },
    },
]
