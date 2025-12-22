# Canvas App Tools

Custom tool implementations for the NormCode Canvas application.

## Overview

These tools are designed to integrate with the Canvas app's architecture:
- **WebSocket-based communication** for real-time updates
- **Async-friendly** design for FastAPI integration
- **Event emission** for UI monitoring

## Tools

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

user_input = CanvasUserInputTool(event_emitter)
body.user_input = user_input
```

### CanvasFileSystemTool

A file system tool that emits WebSocket events for file operations.

Features:
- Emits `file:read`, `file:write`, `file:list` events
- Allows UI to show file operation progress
- Same interface as standard FileSystemTool

```python
from tools import CanvasFileSystemTool

file_system = CanvasFileSystemTool(base_dir, event_emitter)
body.file_system = file_system
```

## Integration with Agent Registry

These tools can be injected into Body instances via the AgentRegistry:

```python
from services.agent_service import agent_registry
from tools import CanvasUserInputTool

# Register tool callback to inject custom tools
def customize_body(body, agent_id):
    body.user_input = CanvasUserInputTool(...)
    return body
```

## Future Enhancements

- [ ] Code editor integration for user input
- [ ] File diff visualization
- [ ] Approval workflows for sensitive operations
- [ ] Cost/token tracking per tool call
