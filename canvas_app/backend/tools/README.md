# Canvas App Tools

Custom tool implementations for the NormCode Canvas application.

## Overview

These tools are designed to integrate with the Canvas app's architecture:
- **WebSocket-based communication** for real-time updates
- **Async-friendly** design for FastAPI integration
- **Event emission** for UI monitoring
- **Self-contained** - can work with or without infra dependencies

## Tools

### CanvasLLMTool

A Language Model tool that emits WebSocket events for LLM operations.

Features:
- Emits `llm:call_started`, `llm:call_completed`, `llm:call_failed` events
- Shows prompt previews and response previews in UI
- Tracks call duration and token usage
- Same interface as infra LanguageModel
- Falls back to mock mode if API keys not available

```python
from tools import CanvasLLMTool

# Create LLM with WebSocket event emission
llm = CanvasLLMTool(
    model_name="qwen-plus",
    emit_callback=lambda event, data: websocket.emit(event, data)
)

# Use like standard LanguageModel
response = llm.generate("Hello, world!")

# Create generation functions
gen_fn = llm.create_generation_function("Translate: $text")
result = gen_fn({"text": "Hello"})
```

WebSocket Events:
- `llm:call_started`: Emitted when LLM call begins (includes prompt preview)
- `llm:call_completed`: Emitted when call succeeds (includes response preview, duration)
- `llm:call_failed`: Emitted when call fails (includes error message)

### CanvasUserInputTool

A user input tool for human-in-the-loop orchestration that uses WebSocket events.

When user input is needed:
1. Tool emits a `user_input:request` WebSocket event
2. Execution pauses waiting for response
3. Frontend shows a UI form for user input
4. User submits response via REST API
5. Tool receives response and continues execution

```python
from tools import CanvasUserInputTool

user_input = CanvasUserInputTool(emit_callback=event_emitter)
body.user_input = user_input
```

WebSocket Events:
- `user_input:request`: Emitted when input is needed
- `user_input:completed`: Emitted when user submits response
- `user_input:cancelled`: Emitted when request is cancelled

### CanvasFileSystemTool

A file system tool that emits WebSocket events for file operations.

Features:
- Emits `file:operation` events for read/write/list/delete
- Allows UI to show file operation progress
- Same interface as standard FileSystemTool

```python
from tools import CanvasFileSystemTool

file_system = CanvasFileSystemTool(
    base_dir="/path/to/project",
    emit_callback=event_emitter
)
body.file_system = file_system
```

WebSocket Events:
- `file:operation`: Emitted for all file operations (status: started/completed/failed)

## Integration with Agent Registry

These tools can be injected into Body instances via the AgentRegistry:

```python
from services.agent_service import agent_registry
from tools import CanvasUserInputTool, CanvasFileSystemTool, CanvasLLMTool

# Create tools with event emission
def create_canvas_tools(emit_callback):
    return {
        "llm": CanvasLLMTool(model_name="qwen-plus", emit_callback=emit_callback),
        "file_system": CanvasFileSystemTool(base_dir=".", emit_callback=emit_callback),
        "user_input": CanvasUserInputTool(emit_callback=emit_callback),
    }
```

## Utility Functions

### get_available_llm_models

Get list of available LLM models from settings.yaml.

```python
from tools import get_available_llm_models

models = get_available_llm_models()
# Returns: ["demo", "qwen-plus", "gpt-4o", ...]
```

### CanvasPythonInterpreterTool

A Python interpreter tool that emits WebSocket events for script execution.

Features:
- Emits `python:execution_started`, `python:execution_completed`, `python:execution_failed` events
- Emits `python:function_started`, `python:function_completed`, `python:function_failed` events
- Shows code preview and execution results in UI
- Same interface as infra PythonInterpreterTool
- Supports Body injection for script access to tools

```python
from tools import CanvasPythonInterpreterTool

# Create interpreter with WebSocket event emission
python = CanvasPythonInterpreterTool(
    emit_callback=lambda event, data: websocket.emit(event, data),
    body=body  # Optional - gives scripts access to tools
)

# Execute script code
result = python.execute(
    script_code="result = x + y",
    inputs={"x": 1, "y": 2}
)

# Execute a specific function
result = python.function_execute(
    script_code="def add(a, b): return a + b",
    function_name="add",
    function_params={"a": 1, "b": 2}
)

# Create a reusable executor
executor = python.create_function_executor(script_code, "process")
result = executor({"data": my_data})
```

WebSocket Events:
- `python:execution_started`: Script execution begins
- `python:execution_completed`: Script executed successfully
- `python:execution_failed`: Script failed with error
- `python:function_started`: Function execution begins
- `python:function_completed`: Function executed successfully
- `python:function_failed`: Function failed with error

### CanvasPromptTool

A prompt template tool that emits WebSocket events for template operations.

Features:
- Emits `prompt:read_started`, `prompt:read_completed`, `prompt:read_failed` events
- Emits `prompt:render_started`, `prompt:render_completed`, `prompt:render_failed` events
- Shows template previews and rendered output previews
- Same interface as infra PromptTool
- Caches templates for performance

```python
from tools import CanvasPromptTool

# Create prompt tool with WebSocket event emission
prompt_tool = CanvasPromptTool(
    base_dir="/path/to/prompts",
    emit_callback=lambda event, data: websocket.emit(event, data)
)

# Read a template
template = prompt_tool.read("instruction.md")

# Render with variables
rendered = prompt_tool.render("instruction.md", {"task": "Analyze data"})

# Create a template function
template_fn = prompt_tool.create_template_function(template)
result = template_fn({"task": "Analyze"})
```

WebSocket Events:
- `prompt:read_started`: Template loading begins
- `prompt:read_completed`: Template loaded successfully
- `prompt:read_failed`: Template loading failed
- `prompt:render_started`: Rendering begins
- `prompt:render_completed`: Rendering succeeded
- `prompt:render_failed`: Rendering failed
- `prompt:substitute`: Variable substitution occurred
- `prompt:cache_cleared`: Cache was cleared

## Future Enhancements

- [x] LLM tool with WebSocket events
- [x] Python interpreter tool wrapper
- [ ] Code editor integration for user input
- [ ] File diff visualization
- [ ] Approval workflows for sensitive operations
- [ ] Cost/token tracking per tool call
