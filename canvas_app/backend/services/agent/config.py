"""Agent and Mapping Configuration Dataclasses.

This module contains the core configuration classes for the agent system:
- AgentConfig: Configuration for a single agent/body (tool-centric design)
- Tool configuration dataclasses (LLMToolConfig, FileSystemToolConfig, etc.)
- MappingRule: Rule for mapping inferences to agents
- LLMProviderRef: Reference to an LLM provider (inline or by ID)
- ProjectAgentConfig: Project-specific agent configuration file

These are pure data classes with no dependencies on other services.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

# File suffix for project agent configuration files
AGENT_CONFIG_SUFFIX = ".agent.json"


# =============================================================================
# Tool Configuration Dataclasses
# Each tool is a peer - LLM is just another tool like file_system or paradigm
# =============================================================================

@dataclass
class LLMToolConfig:
    """Configuration for the LLM tool."""
    model: str = "demo"  # Model name (references global LLM settings)
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"model": self.model}
        if self.temperature != 0.0:
            result["temperature"] = self.temperature
        if self.max_tokens:
            result["max_tokens"] = self.max_tokens
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMToolConfig':
        if data is None:
            return cls()
        return cls(
            model=data.get("model", "demo"),
            temperature=data.get("temperature", 0.0),
            max_tokens=data.get("max_tokens"),
        )


@dataclass
class ParadigmToolConfig:
    """Configuration for the paradigm tool."""
    dir: Optional[str] = None  # Custom paradigm directory (relative to project)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.dir:
            result["dir"] = self.dir
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParadigmToolConfig':
        if data is None:
            return cls()
        return cls(dir=data.get("dir"))


@dataclass
class FileSystemToolConfig:
    """Configuration for the file system tool."""
    enabled: bool = True
    base_dir: Optional[str] = None  # Base directory for file operations
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"enabled": self.enabled}
        if self.base_dir:
            result["base_dir"] = self.base_dir
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileSystemToolConfig':
        if data is None:
            return cls()
        return cls(
            enabled=data.get("enabled", True),
            base_dir=data.get("base_dir"),
        )


@dataclass
class PythonInterpreterToolConfig:
    """Configuration for the Python interpreter tool."""
    enabled: bool = True
    timeout: int = 30  # Execution timeout in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "timeout": self.timeout,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PythonInterpreterToolConfig':
        if data is None:
            return cls()
        return cls(
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 30),
        )


@dataclass
class UserInputToolConfig:
    """Configuration for the user input tool."""
    enabled: bool = True
    mode: str = "blocking"  # blocking, async, disabled
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInputToolConfig':
        if data is None:
            return cls()
        return cls(
            enabled=data.get("enabled", True),
            mode=data.get("mode", "blocking"),
        )


@dataclass
class CustomToolConfig:
    """
    Configuration for a custom/injectable tool.
    
    This allows injecting additional tools via JSON configuration.
    The tool must be registered in the ToolRegistry with the given type_id.
    
    Example:
    {
        "type_id": "my_custom_parser",
        "enabled": true,
        "settings": {
            "language": "python",
            "strict_mode": true
        }
    }
    """
    type_id: str  # Implementation identifier (must be registered in ToolFactory)
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type_id": self.type_id,
            "enabled": self.enabled,
            "settings": self.settings,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomToolConfig':
        if data is None:
            return cls(type_id="unknown")
        return cls(
            type_id=data.get("type_id", "unknown"),
            enabled=data.get("enabled", True),
            settings=data.get("settings", {}),
        )


@dataclass
class AgentToolsConfig:
    """
    Container for all tool configurations.
    
    Architecture:
    ┌─────────────────────────────────────────────────────────────────────┐
    │                        AgentToolsConfig                             │
    │                                                                     │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
    │  │ llm         │  │ file_system │  │ paradigm    │  (core tools)   │
    │  │  - model    │  │  - base_dir │  │  - dir      │                 │
    │  │  - temp     │  │  - enabled  │  │             │                 │
    │  └─────────────┘  └─────────────┘  └─────────────┘                 │
    │                                                                     │
    │  ┌─────────────┐  ┌─────────────┐                                  │
    │  │ python_int. │  │ user_input  │  (core tools)                    │
    │  │  - timeout  │  │  - mode     │                                  │
    │  └─────────────┘  └─────────────┘                                  │
    │                                                                     │
    │  ┌────────────────────────────────────────────────────────────┐    │
    │  │ custom: Dict[str, CustomToolConfig]                        │    │
    │  │   - "my_parser": { type_id: "custom_parser", settings... } │    │
    │  │   - "rag_tool": { type_id: "rag", settings... }            │    │
    │  └────────────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────────────┘
    
    Each tool is a peer - LLM is treated the same as file_system, paradigm, etc.
    Custom tools can be injected via the 'custom' dict.
    """
    # Core tools (always available, can be configured)
    llm: LLMToolConfig = field(default_factory=LLMToolConfig)
    paradigm: ParadigmToolConfig = field(default_factory=ParadigmToolConfig)
    file_system: FileSystemToolConfig = field(default_factory=FileSystemToolConfig)
    python_interpreter: PythonInterpreterToolConfig = field(default_factory=PythonInterpreterToolConfig)
    user_input: UserInputToolConfig = field(default_factory=UserInputToolConfig)
    
    # Custom/injectable tools (extensibility point)
    # Key is tool name, value is the tool configuration
    custom: Dict[str, CustomToolConfig] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "llm": self.llm.to_dict(),
            "paradigm": self.paradigm.to_dict(),
            "file_system": self.file_system.to_dict(),
            "python_interpreter": self.python_interpreter.to_dict(),
            "user_input": self.user_input.to_dict(),
        }
        if self.custom:
            result["custom"] = {k: v.to_dict() for k, v in self.custom.items()}
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentToolsConfig':
        if data is None:
            return cls()
        
        # Parse custom tools
        custom_data = data.get("custom", {})
        custom_tools = {
            name: CustomToolConfig.from_dict(cfg)
            for name, cfg in custom_data.items()
        }
        
        return cls(
            llm=LLMToolConfig.from_dict(data.get("llm")),
            paradigm=ParadigmToolConfig.from_dict(data.get("paradigm")),
            file_system=FileSystemToolConfig.from_dict(data.get("file_system")),
            python_interpreter=PythonInterpreterToolConfig.from_dict(data.get("python_interpreter")),
            user_input=UserInputToolConfig.from_dict(data.get("user_input")),
            custom=custom_tools,
        )
    
    def get_tool_names(self) -> List[str]:
        """Get all configured tool names (core + custom)."""
        core = ["llm", "paradigm", "file_system", "python_interpreter", "user_input"]
        return core + list(self.custom.keys())


@dataclass
class AgentConfig:
    """
    Configuration for a single agent.
    
    An agent represents a configured Body instance with specific tool settings.
    All tools (including LLM) are peers within the 'tools' configuration.
    
    Example JSON:
    {
        "id": "fast-agent",
        "name": "Fast Agent",
        "tools": {
            "llm": { "model": "qwen-turbo" },
            "paradigm": { "dir": "provisions/paradigms" },
            "file_system": { "enabled": true, "base_dir": "." },
            "python_interpreter": { "enabled": false },
            "user_input": { "enabled": true, "mode": "async" }
        }
    }
    """
    id: str
    name: str
    description: str = ""
    tools: AgentToolsConfig = field(default_factory=AgentToolsConfig)
    
    # =========================================================================
    # Convenience properties for backward compatibility and easy access
    # =========================================================================
    
    @property
    def llm_model(self) -> str:
        """Get the LLM model (convenience property)."""
        return self.tools.llm.model
    
    @property
    def paradigm_dir(self) -> Optional[str]:
        """Get the paradigm directory (convenience property)."""
        return self.tools.paradigm.dir
    
    @property
    def file_system_enabled(self) -> bool:
        """Check if file system is enabled (convenience property)."""
        return self.tools.file_system.enabled
    
    @property
    def file_system_base_dir(self) -> Optional[str]:
        """Get file system base directory (convenience property)."""
        return self.tools.file_system.base_dir
    
    @property
    def python_interpreter_enabled(self) -> bool:
        """Check if Python interpreter is enabled (convenience property)."""
        return self.tools.python_interpreter.enabled
    
    @property
    def python_interpreter_timeout(self) -> int:
        """Get Python interpreter timeout (convenience property)."""
        return self.tools.python_interpreter.timeout
    
    @property
    def user_input_enabled(self) -> bool:
        """Check if user input is enabled (convenience property)."""
        return self.tools.user_input.enabled
    
    @property
    def user_input_mode(self) -> str:
        """Get user input mode (convenience property)."""
        return self.tools.user_input.mode
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tools": self.tools.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create from dictionary.
        
        Supports both new tool-centric format and legacy flat format for
        backward compatibility.
        """
        # Check if using new tools-based format
        if "tools" in data:
            return cls(
                id=data.get("id", ""),
                name=data.get("name", ""),
                description=data.get("description", ""),
                tools=AgentToolsConfig.from_dict(data.get("tools")),
            )
        
        # Legacy format - convert flat fields to tool-centric structure
        tools = AgentToolsConfig(
            llm=LLMToolConfig(
                model=data.get("llm_model", "demo"),
            ),
            paradigm=ParadigmToolConfig(
                dir=data.get("paradigm_dir"),
            ),
            file_system=FileSystemToolConfig(
                enabled=data.get("file_system_enabled", True),
                base_dir=data.get("file_system_base_dir"),
            ),
            python_interpreter=PythonInterpreterToolConfig(
                enabled=data.get("python_interpreter_enabled", True),
                timeout=data.get("python_interpreter_timeout", 30),
            ),
            user_input=UserInputToolConfig(
                enabled=data.get("user_input_enabled", True),
                mode=data.get("user_input_mode", "blocking"),
            ),
        )
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tools=tools,
        )


@dataclass
class MappingRule:
    """Rule for mapping inferences to agents.
    
    Rules are evaluated in priority order (highest first) to determine
    which agent should handle a given inference.
    """
    match_type: str  # 'flow_index', 'concept_name', 'sequence_type'
    pattern: str     # Regex pattern
    agent_id: str
    priority: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_type": self.match_type,
            "pattern": self.pattern,
            "agent_id": self.agent_id,
            "priority": self.priority,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MappingRule':
        return cls(
            match_type=data.get("match_type", "flow_index"),
            pattern=data.get("pattern", ".*"),
            agent_id=data.get("agent_id", "default"),
            priority=data.get("priority", 0),
        )


@dataclass
class LLMProviderRef:
    """
    Reference to an LLM provider for project-specific configuration.
    
    Can either reference a global provider by ID, or define an inline
    provider configuration specific to the project.
    """
    # Reference to a global provider (by ID or name)
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    
    # Inline provider config (if not referencing global)
    provider_type: Optional[str] = None  # openai, anthropic, dashscope, etc.
    api_key: Optional[str] = None  # Can use ${ENV_VAR} syntax
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.provider_id:
            result["provider_id"] = self.provider_id
        if self.provider_name:
            result["provider_name"] = self.provider_name
        if self.provider_type:
            result["provider_type"] = self.provider_type
        if self.api_key:
            result["api_key"] = self.api_key
        if self.base_url:
            result["base_url"] = self.base_url
        if self.model:
            result["model"] = self.model
        if self.temperature != 0.0:
            result["temperature"] = self.temperature
        if self.max_tokens:
            result["max_tokens"] = self.max_tokens
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMProviderRef':
        return cls(
            provider_id=data.get("provider_id"),
            provider_name=data.get("provider_name"),
            provider_type=data.get("provider_type"),
            api_key=data.get("api_key"),
            base_url=data.get("base_url"),
            model=data.get("model"),
            temperature=data.get("temperature", 0.0),
            max_tokens=data.get("max_tokens"),
        )
    
    @property
    def is_inline(self) -> bool:
        """Check if this is an inline provider (vs reference to global)."""
        return self.provider_type is not None or self.model is not None


@dataclass
class ProjectAgentConfig:
    """
    Project-specific agent configuration.
    
    Stored as {project-name}.agent.json alongside the project config.
    Contains agents, mappings, and optionally LLM providers specific
    to this project.
    
    Example file: compiler.agent.json
    {
        "default_agent": "compiler-main",
        "agents": [
            {
                "id": "compiler-main",
                "name": "Compiler Agent",
                "llm_model": "qwen-plus",
                "python_interpreter_enabled": false
            }
        ],
        "mappings": [
            {
                "match_type": "flow_index",
                "pattern": "1\\..*",
                "agent_id": "compiler-main"
            }
        ],
        "llm_providers": [
            {
                "provider_name": "project-llm",
                "provider_type": "dashscope",
                "model": "qwen-turbo-latest"
            }
        ]
    }
    """
    # Default agent for this project (if not mapped by rules)
    default_agent: Optional[str] = None
    
    # Agents defined for this project
    agents: List[AgentConfig] = field(default_factory=list)
    
    # Mapping rules for this project
    mappings: List[MappingRule] = field(default_factory=list)
    
    # Project-specific LLM providers (optional)
    llm_providers: List[LLMProviderRef] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        
        if self.default_agent:
            result["default_agent"] = self.default_agent
        
        if self.agents:
            result["agents"] = [a.to_dict() for a in self.agents]
        
        if self.mappings:
            result["mappings"] = [m.to_dict() for m in self.mappings]
        
        if self.llm_providers:
            result["llm_providers"] = [p.to_dict() for p in self.llm_providers]
        
        if self.description:
            result["description"] = self.description
        
        if self.created_at:
            result["created_at"] = self.created_at
        if self.updated_at:
            result["updated_at"] = self.updated_at
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectAgentConfig':
        """Create from dictionary."""
        agents = [AgentConfig.from_dict(a) for a in data.get("agents", [])]
        mappings = [MappingRule.from_dict(m) for m in data.get("mappings", [])]
        llm_providers = [LLMProviderRef.from_dict(p) for p in data.get("llm_providers", [])]
        
        return cls(
            default_agent=data.get("default_agent"),
            agents=agents,
            mappings=mappings,
            llm_providers=llm_providers,
            description=data.get("description", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


def get_agent_config_filename(project_name: str) -> str:
    """
    Get the agent config filename for a project.
    Converts project name to a safe filename slug.
    """
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    slug = project_name.lower().strip()
    slug = slug.replace(' ', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    slug = slug.strip('-')
    return f"{slug}{AGENT_CONFIG_SUFFIX}"

