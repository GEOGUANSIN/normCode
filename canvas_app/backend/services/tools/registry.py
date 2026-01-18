"""
Tool Registry.

Manages the lifecycle of tool instances:
- Registers available tool implementations
- Creates and caches tool instances
- Provides tool discovery for UI
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
import logging

from .factory import ToolFactory, ToolConfig, ToolType

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """
    Definition of a tool that can be used.
    
    This is the "blueprint" for a tool, separate from its runtime configuration.
    """
    tool_type: ToolType
    type_id: str  # Implementation identifier
    name: str
    description: str
    schema: Dict[str, Any] = field(default_factory=dict)  # JSON schema for settings
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_type": self.tool_type.value,
            "type_id": self.type_id,
            "name": self.name,
            "description": self.description,
            "schema": self.schema,
            "tags": self.tags,
        }


class ToolRegistry:
    """
    Registry for managing tools.
    
    Responsibilities:
    1. Track available tool definitions (blueprints)
    2. Create tool instances from configurations
    3. Cache tool instances for reuse
    4. Provide discovery API for UI
    
    Architecture:
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                      TOOL REGISTRY                               │
    │                                                                  │
    │  ┌──────────────────┐     ┌──────────────────┐                  │
    │  │ Tool Definitions │     │ Tool Instances   │                  │
    │  │ (blueprints)     │     │ (cached)         │                  │
    │  │                  │     │                  │                  │
    │  │ - llm/openai     │     │ agent1.llm →     │                  │
    │  │ - llm/dashscope  │     │   <OpenAILLM>    │                  │
    │  │ - file_system    │     │                  │                  │
    │  │ - python_interp  │     │ agent2.llm →     │                  │
    │  │ - canvas         │     │   <DashScopeLLM> │                  │
    │  │ - chat           │     │                  │                  │
    │  └──────────────────┘     └──────────────────┘                  │
    │                                                                  │
    │  Factory: config → instance                                      │
    └─────────────────────────────────────────────────────────────────┘
    ```
    """
    
    def __init__(self):
        # Tool definitions (blueprints)
        self._definitions: Dict[str, ToolDefinition] = {}  # key: "{tool_type}/{type_id}"
        
        # Cached tool instances per agent
        # key: "{agent_id}.{tool_type}", value: tool instance
        self._instances: Dict[str, Any] = {}
        
        # Initialize default tool definitions
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default tool implementations."""
        # LLM tools
        self.register_definition(ToolDefinition(
            tool_type=ToolType.LLM,
            type_id="canvas",
            name="Canvas LLM",
            description="LLM tool integrated with canvas providers",
            schema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Model name"},
                    "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                    "max_tokens": {"type": "integer", "minimum": 1},
                },
            },
            tags=["llm", "canvas", "default"],
        ))
        
        # File system tool
        self.register_definition(ToolDefinition(
            tool_type=ToolType.FILE_SYSTEM,
            type_id="default",
            name="File System",
            description="Read/write files in the workspace",
            schema={
                "type": "object",
                "properties": {
                    "base_dir": {"type": "string", "description": "Base directory"},
                    "enabled": {"type": "boolean"},
                },
            },
            tags=["file", "io", "default"],
        ))
        
        # Python interpreter
        self.register_definition(ToolDefinition(
            tool_type=ToolType.PYTHON_INTERPRETER,
            type_id="default",
            name="Python Interpreter",
            description="Execute Python code",
            schema={
                "type": "object",
                "properties": {
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 300},
                    "enabled": {"type": "boolean"},
                },
            },
            tags=["python", "code", "default"],
        ))
        
        # User input tool
        self.register_definition(ToolDefinition(
            tool_type=ToolType.USER_INPUT,
            type_id="default",
            name="User Input",
            description="Request input from the user",
            schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["blocking", "async", "disabled"]},
                    "enabled": {"type": "boolean"},
                },
            },
            tags=["user", "input", "default"],
        ))
        
        # Paradigm tool
        self.register_definition(ToolDefinition(
            tool_type=ToolType.PARADIGM,
            type_id="default",
            name="Paradigm",
            description="Domain-specific paradigm for code generation",
            schema={
                "type": "object",
                "properties": {
                    "dir": {"type": "string", "description": "Paradigm directory"},
                },
            },
            tags=["paradigm", "domain", "default"],
        ))
        
        # Canvas tools (app-specific)
        self.register_definition(ToolDefinition(
            tool_type=ToolType.CANVAS,
            type_id="default",
            name="Canvas Tool",
            description="Manipulate the canvas UI",
            tags=["canvas", "ui", "default"],
        ))
        
        self.register_definition(ToolDefinition(
            tool_type=ToolType.CHAT,
            type_id="default",
            name="Chat Tool",
            description="Send messages to chat",
            tags=["chat", "ui", "default"],
        ))
        
        self.register_definition(ToolDefinition(
            tool_type=ToolType.PARSER,
            type_id="default",
            name="Parser Tool",
            description="Parse code and extract structure",
            tags=["parser", "code", "default"],
        ))
    
    def register_definition(self, definition: ToolDefinition) -> None:
        """Register a tool definition (blueprint)."""
        key = f"{definition.tool_type.value}/{definition.type_id}"
        self._definitions[key] = definition
        logger.debug(f"Registered tool definition: {key}")
    
    def get_definition(self, tool_type: ToolType, type_id: str) -> Optional[ToolDefinition]:
        """Get a tool definition by type and implementation."""
        key = f"{tool_type.value}/{type_id}"
        return self._definitions.get(key)
    
    def list_definitions(
        self,
        tool_type: Optional[ToolType] = None,
        tags: Optional[List[str]] = None,
    ) -> List[ToolDefinition]:
        """
        List available tool definitions.
        
        Args:
            tool_type: Filter by tool type
            tags: Filter by tags (any match)
        """
        results = []
        for definition in self._definitions.values():
            if tool_type and definition.tool_type != tool_type:
                continue
            if tags and not any(t in definition.tags for t in tags):
                continue
            results.append(definition)
        return results
    
    def create_tool(
        self,
        agent_id: str,
        tool_type: ToolType,
        config: ToolConfig,
        force_new: bool = False,
    ) -> Any:
        """
        Create or get a cached tool instance for an agent.
        
        Args:
            agent_id: The agent this tool belongs to
            tool_type: Type of tool to create
            config: Tool configuration
            force_new: Force creation of new instance (invalidate cache)
            
        Returns:
            Configured tool instance
        """
        cache_key = f"{agent_id}.{tool_type.value}"
        
        if not force_new and cache_key in self._instances:
            logger.debug(f"Returning cached tool: {cache_key}")
            return self._instances[cache_key]
        
        # Create new instance via factory
        tool = ToolFactory.create(tool_type, config)
        self._instances[cache_key] = tool
        
        logger.info(f"Created tool instance: {cache_key} (impl={config.type_id})")
        return tool
    
    def get_tool(self, agent_id: str, tool_type: ToolType) -> Optional[Any]:
        """Get a cached tool instance."""
        cache_key = f"{agent_id}.{tool_type.value}"
        return self._instances.get(cache_key)
    
    def invalidate_agent_tools(self, agent_id: str) -> None:
        """Invalidate all cached tools for an agent."""
        keys_to_remove = [k for k in self._instances if k.startswith(f"{agent_id}.")]
        for key in keys_to_remove:
            del self._instances[key]
        logger.info(f"Invalidated {len(keys_to_remove)} tools for agent '{agent_id}'")
    
    def invalidate_all(self) -> None:
        """Invalidate all cached tool instances."""
        count = len(self._instances)
        self._instances.clear()
        logger.info(f"Invalidated all {count} cached tool instances")
    
    def get_tool_types(self) -> List[str]:
        """Get all registered tool types."""
        types: Set[str] = set()
        for definition in self._definitions.values():
            types.add(definition.tool_type.value)
        return sorted(types)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize registry state for debugging."""
        return {
            "definitions": [d.to_dict() for d in self._definitions.values()],
            "cached_instances": list(self._instances.keys()),
        }


# Global singleton
tool_registry = ToolRegistry()

