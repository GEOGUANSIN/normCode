"""
Default Tool Factories.

Registers the default implementations for each tool type.
These are the standard tools that come with the canvas app.
"""

import logging
from typing import Any, Dict

from .factory import ToolFactory, ToolType

logger = logging.getLogger(__name__)


def create_canvas_llm(settings: Dict[str, Any]) -> Any:
    """
    Create a Canvas LLM tool.
    
    This is the default LLM implementation that integrates with
    the canvas app's LLM provider system.
    """
    from tools.llm_tool import CanvasLLMTool
    
    model = settings.get("model", "qwen-plus")
    temperature = settings.get("temperature")
    max_tokens = settings.get("max_tokens")
    
    return CanvasLLMTool(
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_file_system_tool(settings: Dict[str, Any]) -> Any:
    """
    Create a file system tool.
    
    This wraps the infra's file system tool with canvas-specific
    configuration.
    """
    try:
        from infra._agent._tools import FileSystemTool
    except ImportError:
        # Fallback: return a stub
        logger.warning("Could not import FileSystemTool from infra")
        return None
    
    base_dir = settings.get("base_dir", ".")
    enabled = settings.get("enabled", True)
    
    tool = FileSystemTool(base_dir=base_dir)
    tool.enabled = enabled
    return tool


def create_python_interpreter_tool(settings: Dict[str, Any]) -> Any:
    """
    Create a Python interpreter tool.
    """
    try:
        from infra._agent._tools import PythonInterpreterTool
    except ImportError:
        logger.warning("Could not import PythonInterpreterTool from infra")
        return None
    
    timeout = settings.get("timeout", 30)
    enabled = settings.get("enabled", True)
    
    tool = PythonInterpreterTool(timeout=timeout)
    tool.enabled = enabled
    return tool


def create_user_input_tool(settings: Dict[str, Any]) -> Any:
    """
    Create a user input tool.
    
    Note: The canvas app typically replaces this with CanvasUserInputTool
    during tool injection.
    """
    try:
        from infra._agent._tools import UserInputTool
    except ImportError:
        logger.warning("Could not import UserInputTool from infra")
        return None
    
    mode = settings.get("mode", "blocking")
    enabled = settings.get("enabled", True)
    
    tool = UserInputTool()
    tool.enabled = enabled
    tool.mode = mode
    return tool


def create_paradigm_tool(settings: Dict[str, Any]) -> Any:
    """
    Create a paradigm tool for domain-specific code generation.
    """
    paradigm_dir = settings.get("dir")
    if not paradigm_dir:
        return None
    
    base_dir = settings.get("base_dir", ".")
    
    try:
        from infra._tools._paradigm_use.paradigm_tool import ParadigmTool
        from pathlib import Path
        
        paradigm_path = Path(paradigm_dir)
        if not paradigm_path.is_absolute():
            paradigm_path = Path(base_dir) / paradigm_path
        
        if paradigm_path.exists():
            return ParadigmTool(paradigm_dir=str(paradigm_path))
        else:
            logger.warning(f"Paradigm directory not found: {paradigm_path}")
            return None
    except ImportError:
        logger.warning("Could not import ParadigmTool from infra")
        return None


def create_canvas_tool(settings: Dict[str, Any]) -> Any:
    """
    Create the canvas manipulation tool.
    
    Note: This is typically created and injected by the execution controller
    as it requires WebSocket event emission.
    """
    # Canvas tool requires event_emitter, will be created during injection
    return None


def create_chat_tool(settings: Dict[str, Any]) -> Any:
    """
    Create the chat tool.
    
    Note: This is typically created and injected by the execution controller.
    """
    # Chat tool requires event_emitter, will be created during injection
    return None


def create_parser_tool(settings: Dict[str, Any]) -> Any:
    """
    Create the parser tool.
    """
    try:
        from tools.parser_tool import ParserTool
        return ParserTool()
    except ImportError:
        logger.warning("Could not import ParserTool")
        return None


def register_default_factories() -> None:
    """
    Register all default tool factories.
    
    This should be called during app initialization.
    """
    logger.info("Registering default tool factories...")
    
    # LLM
    ToolFactory.register(ToolType.LLM, "canvas", create_canvas_llm, is_default=True)
    
    # Core tools
    ToolFactory.register(ToolType.FILE_SYSTEM, "default", create_file_system_tool, is_default=True)
    ToolFactory.register(ToolType.PYTHON_INTERPRETER, "default", create_python_interpreter_tool, is_default=True)
    ToolFactory.register(ToolType.USER_INPUT, "default", create_user_input_tool, is_default=True)
    ToolFactory.register(ToolType.PARADIGM, "default", create_paradigm_tool, is_default=True)
    
    # Canvas-specific tools
    ToolFactory.register(ToolType.CANVAS, "default", create_canvas_tool, is_default=True)
    ToolFactory.register(ToolType.CHAT, "default", create_chat_tool, is_default=True)
    ToolFactory.register(ToolType.PARSER, "default", create_parser_tool, is_default=True)
    
    logger.info("Default tool factories registered")


# Auto-register on import
register_default_factories()

