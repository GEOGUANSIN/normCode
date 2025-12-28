"""Agent Registry and Customization Service.

This module provides backward-compatible exports from the refactored
agent sub-package. All functionality has been moved to:

- services/agent/config.py - AgentConfig, MappingRule
- services/agent/monitoring.py - ToolCallEvent, MonitoredToolProxy
- services/agent/mapping.py - AgentMappingService
- services/agent/registry.py - AgentRegistry
- services/agent/llm_providers.py - LLMSettingsService

This file is a facade that re-exports all public APIs for backward
compatibility with existing code.
"""

# Re-export everything from the agent sub-package
from services.agent import (
    # Config dataclasses
    AgentConfig,
    MappingRule,
    
    # Monitoring
    ToolCallEvent,
    MonitoredToolProxy,
    
    # Mapping service
    AgentMappingService,
    agent_mapping,
    
    # Registry
    AgentRegistry,
    agent_registry,
)

__all__ = [
    # Config dataclasses
    'AgentConfig',
    'MappingRule',
    
    # Monitoring
    'ToolCallEvent',
    'MonitoredToolProxy',
    
    # Mapping service
    'AgentMappingService',
    'agent_mapping',
    
    # Registry
    'AgentRegistry',
    'agent_registry',
]
