"""
Canvas App Tools - Custom tool implementations for the Canvas application.

These tools integrate with the Canvas app's WebSocket-based architecture
to provide real-time feedback and human-in-the-loop capabilities.

Tools:
- CanvasUserInputTool: WebSocket-based user input for human-in-the-loop
- CanvasFileSystemTool: File system with WebSocket notifications
- CanvasLLMTool: LLM with WebSocket notifications for prompts/responses
- CanvasPythonInterpreterTool: Python execution with WebSocket notifications
- CanvasPromptTool: Prompt template tool with WebSocket notifications
- CanvasChatTool: Chat interface for compiler-user interaction
- CanvasDisplayTool: Display artifacts on the Canvas (source, structure, graph)
- CanvasFormatterTool: Data formatting and parsing for paradigm composition
- CanvasCompositionTool: Function composition for paradigm execution
"""

from .user_input_tool import CanvasUserInputTool
from .file_system_tool import CanvasFileSystemTool
from .llm_tool import CanvasLLMTool, get_available_llm_models
from .python_interpreter_tool import CanvasPythonInterpreterTool
from .prompt_tool import CanvasPromptTool
from .chat_tool import CanvasChatTool
from .canvas_tool import CanvasDisplayTool
from .formatter_tool import CanvasFormatterTool
from .composition_tool import CanvasCompositionTool

__all__ = [
    "CanvasUserInputTool",
    "CanvasFileSystemTool",
    "CanvasLLMTool",
    "CanvasPythonInterpreterTool",
    "CanvasPromptTool",
    "CanvasChatTool",
    "CanvasDisplayTool",
    "CanvasFormatterTool",
    "CanvasCompositionTool",
    "get_available_llm_models",
]
