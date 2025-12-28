"""
Execution service module - manages orchestrator execution with debugging support.

This module is organized into sub-modules for clarity:
- log_handler: Captures and parses orchestrator logs
- paradigm_tool: Custom paradigm loading from project directories
- tool_injection: Tool monitoring and injection for Body
- checkpoint_service: Checkpoint listing, loading, and management
- value_service: Value override and dependency tracking
- controller: Core ExecutionController class

The main execution_service.py file provides the facade and backwards-compatible API.
"""

from .log_handler import OrchestratorLogHandler, attach_log_handlers, detach_log_handlers
from .paradigm_tool import CustomParadigmTool, create_paradigm_tool
from .tool_injection import (
    wrap_body_with_monitoring,
    inject_canvas_tools,
    CanvasToolSet,
    create_tool_event_emitter,
    setup_tool_monitoring,
)
from .checkpoint_service import CheckpointService, checkpoint_service
from .value_service import ValueService, value_service
from .controller import ExecutionController

__all__ = [
    # Controller
    'ExecutionController',
    
    # Log handler
    'OrchestratorLogHandler',
    'attach_log_handlers',
    'detach_log_handlers',
    
    # Paradigm tool
    'CustomParadigmTool',
    'create_paradigm_tool',
    
    # Tool injection
    'wrap_body_with_monitoring',
    'inject_canvas_tools',
    'CanvasToolSet',
    'create_tool_event_emitter',
    'setup_tool_monitoring',
    
    # Checkpoint service
    'CheckpointService',
    'checkpoint_service',
    
    # Value service
    'ValueService',
    'value_service',
]
