"""Agent and Mapping Configuration Dataclasses.

This module contains the core configuration classes for the agent system:
- AgentConfig: Configuration for a single agent/body
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


@dataclass
class AgentConfig:
    """Configuration for a single agent.
    
    An agent represents a configured Body instance with specific tool
    settings and LLM configuration.
    """
    id: str
    name: str
    description: str = ""
    
    # LLM config - references a provider from LLMSettingsService by name/model
    llm_model: str = "qwen-plus"
    
    # Tool config
    file_system_enabled: bool = True
    file_system_base_dir: Optional[str] = None
    python_interpreter_enabled: bool = True
    python_interpreter_timeout: int = 30
    user_input_enabled: bool = True
    user_input_mode: str = "blocking"  # blocking, async, disabled
    
    # Paradigm config
    paradigm_dir: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "llm_model": self.llm_model,
            "file_system_enabled": self.file_system_enabled,
            "file_system_base_dir": self.file_system_base_dir,
            "python_interpreter_enabled": self.python_interpreter_enabled,
            "python_interpreter_timeout": self.python_interpreter_timeout,
            "user_input_enabled": self.user_input_enabled,
            "user_input_mode": self.user_input_mode,
            "paradigm_dir": self.paradigm_dir,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            llm_model=data.get("llm_model", "qwen-plus"),
            file_system_enabled=data.get("file_system_enabled", True),
            file_system_base_dir=data.get("file_system_base_dir"),
            python_interpreter_enabled=data.get("python_interpreter_enabled", True),
            python_interpreter_timeout=data.get("python_interpreter_timeout", 30),
            user_input_enabled=data.get("user_input_enabled", True),
            user_input_mode=data.get("user_input_mode", "blocking"),
            paradigm_dir=data.get("paradigm_dir"),
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

