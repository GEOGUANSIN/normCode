"""
Agent Service Module - Manages agents, mappings, and LLM providers.

This module is organized into sub-modules for clarity:
- config: AgentConfig, MappingRule, ProjectAgentConfig dataclasses
- monitoring: ToolCallEvent, MonitoredToolProxy for tool observation
- mapping: AgentMappingService for inference-to-agent mapping
- registry: AgentRegistry for managing agent configurations and Body instances
- llm_providers: LLMSettingsService for LLM provider configuration
- project_config: ProjectAgentConfigService for project-specific agent configs

The main agent_service.py and llm_settings_service.py files provide
backward-compatible facades to these modules.
"""

from .config import (
    # Tool configuration dataclasses (tool-centric design)
    LLMToolConfig,
    ParadigmToolConfig,
    FileSystemToolConfig,
    PythonInterpreterToolConfig,
    UserInputToolConfig,
    CustomToolConfig,  # For injectable custom tools
    AgentToolsConfig,
    # Agent and project configuration
    AgentConfig,
    MappingRule,
    LLMProviderRef,
    ProjectAgentConfig,
    AGENT_CONFIG_SUFFIX,
    get_agent_config_filename,
)
from .monitoring import ToolCallEvent, MonitoredToolProxy
from .mapping import AgentMappingService, agent_mapping
from .registry import AgentRegistry, agent_registry
from .llm_providers import LLMSettingsService, llm_settings_service
from .project_config import ProjectAgentConfigService, project_agent_config_service

__all__ = [
    # Tool configuration (tool-centric design)
    'LLMToolConfig',
    'ParadigmToolConfig',
    'FileSystemToolConfig',
    'PythonInterpreterToolConfig',
    'UserInputToolConfig',
    'CustomToolConfig',
    'AgentToolsConfig',
    
    # Config dataclasses
    'AgentConfig',
    'MappingRule',
    'LLMProviderRef',
    'ProjectAgentConfig',
    'AGENT_CONFIG_SUFFIX',
    'get_agent_config_filename',
    
    # Monitoring
    'ToolCallEvent',
    'MonitoredToolProxy',
    
    # Mapping service
    'AgentMappingService',
    'agent_mapping',
    
    # Registry
    'AgentRegistry',
    'agent_registry',
    
    # LLM providers
    'LLMSettingsService',
    'llm_settings_service',
    
    # Project agent config
    'ProjectAgentConfigService',
    'project_agent_config_service',
]

