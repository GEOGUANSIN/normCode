"""
Tool Injection - Wraps Body tools with monitoring proxies.

This module provides functionality to:
1. Wrap Body tools with MonitoredToolProxy for real-time monitoring
2. Inject canvas-specific tools (chat, user_input, canvas) into Body

This enables the Agent Panel to show tool calls during execution.
"""

import logging
from typing import Any, Callable, Dict, Optional

from services.agent_service import MonitoredToolProxy, ToolCallEvent, agent_registry
from tools.user_input_tool import CanvasUserInputTool
from tools.chat_tool import CanvasChatTool
from tools.canvas_tool import CanvasDisplayTool

logger = logging.getLogger(__name__)


def wrap_body_with_monitoring(
    body: Any,
    get_flow_index: Callable[[], str],
    emit_tool_event: Callable[[ToolCallEvent], None],
) -> None:
    """
    Wrap a Body's tools with MonitoredToolProxy for real-time monitoring.
    
    This enables the Agent Panel to show tool calls during execution.
    
    Args:
        body: The Body instance to wrap tools on
        get_flow_index: Callback to get current flow index
        emit_tool_event: Callback to emit tool call events
    """
    # Wrap the main tools used during execution
    if hasattr(body, 'llm') and body.llm is not None:
        body.llm = MonitoredToolProxy(
            "default", "llm", body.llm,
            emit_tool_event, get_flow_index
        )
    
    if hasattr(body, 'file_system') and body.file_system is not None:
        body.file_system = MonitoredToolProxy(
            "default", "file_system", body.file_system,
            emit_tool_event, get_flow_index
        )
    
    if hasattr(body, 'python_interpreter') and body.python_interpreter is not None:
        body.python_interpreter = MonitoredToolProxy(
            "default", "python_interpreter", body.python_interpreter,
            emit_tool_event, get_flow_index
        )
    
    if hasattr(body, 'prompt_tool') and body.prompt_tool is not None:
        body.prompt_tool = MonitoredToolProxy(
            "default", "prompt", body.prompt_tool,
            emit_tool_event, get_flow_index
        )
    
    if hasattr(body, 'user_input') and body.user_input is not None:
        body.user_input = MonitoredToolProxy(
            "default", "user_input", body.user_input,
            emit_tool_event, get_flow_index
        )

    if hasattr(body, 'paradigm_tool') and body.paradigm_tool is not None:
        body.paradigm_tool = MonitoredToolProxy(
            "default", "paradigm", body.paradigm_tool,
            emit_tool_event, get_flow_index
        )
    
    if hasattr(body, 'chat') and body.chat is not None:
        body.chat = MonitoredToolProxy(
            "default", "chat", body.chat,
            emit_tool_event, get_flow_index
        )
    
    if hasattr(body, 'canvas') and body.canvas is not None:
        body.canvas = MonitoredToolProxy(
            "default", "canvas", body.canvas,
            emit_tool_event, get_flow_index
        )
    
    # Note: formatter_tool and composition_tool are internal tools used by paradigm
    # execution. They don't benefit from monitoring as they are low-level utilities.
    
    logger.info("Wrapped body tools with monitoring proxies")


class CanvasToolSet:
    """
    Container for canvas-specific tools that can be injected into a Body.
    
    These tools enable human-in-the-loop interactions and canvas operations.
    """
    
    def __init__(self, emit_callback: Callable[[str, Dict], None]):
        """
        Initialize the canvas tool set.
        
        Args:
            emit_callback: Callback to emit WebSocket events
        """
        self.user_input_tool = CanvasUserInputTool(emit_callback=emit_callback)
        self.chat_tool = CanvasChatTool(emit_callback=emit_callback, source="execution")
        self.canvas_tool = CanvasDisplayTool(emit_callback=emit_callback)
    
    def inject_into_body(self, body: Any) -> None:
        """Inject all canvas tools into a Body instance."""
        body.user_input = self.user_input_tool
        body.chat = self.chat_tool
        body.canvas = self.canvas_tool
        logger.info("Injected canvas tools into body")


def inject_canvas_tools(body: Any, emit_callback: Callable[[str, Dict], None]) -> CanvasToolSet:
    """
    Create and inject canvas-specific tools into a Body.
    
    Args:
        body: The Body instance to inject tools into
        emit_callback: Callback to emit WebSocket events
        
    Returns:
        CanvasToolSet containing the created tools
    """
    tool_set = CanvasToolSet(emit_callback)
    tool_set.inject_into_body(body)
    return tool_set


def create_tool_event_emitter(
    emit_threadsafe: Callable[[str, Dict], None],
) -> Callable[[ToolCallEvent], None]:
    """
    Create a tool event emitter callback.
    
    Args:
        emit_threadsafe: Thread-safe emit function
        
    Returns:
        Callback that can be passed to MonitoredToolProxy
    """
    def emit_tool_event(event: ToolCallEvent):
        """Emit tool call event through WebSocket."""
        event_type = f"tool:call_{event.status}"
        emit_threadsafe(event_type, event.to_dict())
        # Also add to agent_registry history for persistence
        agent_registry.tool_call_history.append(event)
        if len(agent_registry.tool_call_history) > agent_registry.max_history:
            agent_registry.tool_call_history = agent_registry.tool_call_history[-agent_registry.max_history:]
    
    return emit_tool_event


def setup_tool_monitoring(
    body: Any,
    get_flow_index: Callable[[], str],
    emit_threadsafe: Callable[[str, Dict], None],
) -> None:
    """
    Complete tool monitoring setup for a Body.
    
    Creates the emit callback and wraps all tools with monitoring proxies.
    
    Args:
        body: The Body instance
        get_flow_index: Callback to get current flow index
        emit_threadsafe: Thread-safe emit function
    """
    emit_tool_event = create_tool_event_emitter(emit_threadsafe)
    wrap_body_with_monitoring(body, get_flow_index, emit_tool_event)

