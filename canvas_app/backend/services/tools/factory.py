"""
Tool Factory System.

Provides:
- ToolType enum for standard tool categories
- ToolConfig dataclass for tool configuration
- ToolFactory for creating tool instances
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable, Type
import logging

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """
    Standard tool types that can be injected into an agent's body.
    
    Core tools (from infra):
    - LLM: Language model for reasoning
    - FILE_SYSTEM: File operations
    - PYTHON_INTERPRETER: Code execution
    - USER_INPUT: Human-in-the-loop input
    - PARADIGM: Domain-specific paradigm
    
    Canvas tools (app-specific):
    - CANVAS: Canvas manipulation
    - CHAT: Chat interface
    - PARSER: Code parsing
    """
    # Core tools
    LLM = "llm"
    FILE_SYSTEM = "file_system"
    PYTHON_INTERPRETER = "python_interpreter"
    USER_INPUT = "user_input"
    PARADIGM = "paradigm"
    
    # Canvas-specific tools
    CANVAS = "canvas"
    CHAT = "chat"
    PARSER = "parser"
    
    # Extension point for custom tools
    CUSTOM = "custom"


@dataclass
class ToolConfig:
    """
    Configuration for a single tool.
    
    This represents what an agent specifies about a tool:
    - type_id: Which implementation to use (e.g., "default", "openai", "custom_impl")
    - enabled: Whether the tool is active
    - settings: Tool-specific configuration passed directly to the tool
    
    Example:
    ```json
    {
        "type_id": "openai",
        "enabled": true,
        "settings": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4096
        }
    }
    ```
    """
    type_id: str = "default"  # Implementation identifier
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type_id": self.type_id,
            "enabled": self.enabled,
            "settings": self.settings,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolConfig":
        return cls(
            type_id=data.get("type_id", "default"),
            enabled=data.get("enabled", True),
            settings=data.get("settings", {}),
        )


# Type alias for tool factory functions
# A factory takes settings dict and returns a tool instance
ToolFactoryFn = Callable[[Dict[str, Any]], Any]


class ToolFactory:
    """
    Factory for creating tool instances.
    
    The factory maintains a registry of tool implementations:
    - Each ToolType can have multiple implementations (e.g., "default", "openai", "custom")
    - Each implementation is a factory function that creates the tool
    
    Usage:
    ```python
    # Register a tool implementation
    ToolFactory.register(ToolType.LLM, "openai", create_openai_llm)
    
    # Create a tool from config
    llm_config = ToolConfig(type_id="openai", settings={"model": "gpt-4"})
    llm_tool = ToolFactory.create(ToolType.LLM, llm_config)
    ```
    """
    
    # Registry: {ToolType: {impl_type_id: factory_fn}}
    _registry: Dict[ToolType, Dict[str, ToolFactoryFn]] = {}
    
    # Default implementations for each tool type
    _defaults: Dict[ToolType, str] = {}
    
    @classmethod
    def register(
        cls,
        tool_type: ToolType,
        type_id: str,
        factory: ToolFactoryFn,
        is_default: bool = False,
    ) -> None:
        """
        Register a tool factory.
        
        Args:
            tool_type: The category of tool (e.g., ToolType.LLM)
            type_id: Identifier for this implementation (e.g., "openai")
            factory: Function that creates the tool from settings dict
            is_default: Whether this is the default implementation
        """
        if tool_type not in cls._registry:
            cls._registry[tool_type] = {}
        
        cls._registry[tool_type][type_id] = factory
        
        if is_default or tool_type not in cls._defaults:
            cls._defaults[tool_type] = type_id
        
        logger.debug(f"Registered tool factory: {tool_type.value}/{type_id}")
    
    @classmethod
    def create(cls, tool_type: ToolType, config: ToolConfig) -> Any:
        """
        Create a tool instance from configuration.
        
        Args:
            tool_type: The category of tool
            config: Tool configuration including implementation type and settings
            
        Returns:
            Configured tool instance
            
        Raises:
            ValueError: If tool type or implementation not found
        """
        if tool_type not in cls._registry:
            raise ValueError(f"Unknown tool type: {tool_type.value}")
        
        type_id = config.type_id
        if type_id == "default":
            type_id = cls._defaults.get(tool_type, "default")
        
        if type_id not in cls._registry[tool_type]:
            available = list(cls._registry[tool_type].keys())
            raise ValueError(
                f"Unknown {tool_type.value} implementation: '{type_id}'. "
                f"Available: {available}"
            )
        
        factory = cls._registry[tool_type][type_id]
        
        try:
            tool = factory(config.settings)
            logger.info(f"Created {tool_type.value} tool with implementation '{type_id}'")
            return tool
        except Exception as e:
            logger.error(f"Failed to create {tool_type.value}/{type_id}: {e}")
            raise
    
    @classmethod
    def get_implementations(cls, tool_type: ToolType) -> list:
        """Get available implementations for a tool type."""
        if tool_type not in cls._registry:
            return []
        return list(cls._registry[tool_type].keys())
    
    @classmethod
    def get_default_implementation(cls, tool_type: ToolType) -> Optional[str]:
        """Get the default implementation for a tool type."""
        return cls._defaults.get(tool_type)
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (for testing)."""
        cls._registry.clear()
        cls._defaults.clear()

