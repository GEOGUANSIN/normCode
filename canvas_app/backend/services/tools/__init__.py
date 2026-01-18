"""
Tool Registry and Factory System.

This module provides a pluggable tool architecture where:
- Tools are registered with their factory functions
- Agents compose tools by referencing them in their config
- Tool settings are applied directly to tools before injection

Architecture:
```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TOOL SYSTEM                                      │
│                                                                         │
│  ┌──────────────────┐                                                  │
│  │  ToolFactory     │  Creates tools from config                       │
│  │  - register()    │  - Factory functions per type/impl               │
│  │  - create()      │  - Settings applied to tool                      │
│  └────────┬─────────┘                                                  │
│           │                                                            │
│           ▼                                                            │
│  ┌──────────────────┐                                                  │
│  │  ToolRegistry    │  Manages tool definitions & instances            │
│  │  - definitions   │  - Blueprints (schema, metadata)                 │
│  │  - instances     │  - Cached per agent                              │
│  └────────┬─────────┘                                                  │
│           │                                                            │
│           ▼                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  AgentConfig.tools                                                │ │
│  │  - llm: { model, temperature }                                    │ │
│  │  - file_system: { base_dir }                                      │ │
│  │  - custom: { "my_tool": { type_id, settings } }                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```
"""

from .registry import (
    ToolRegistry,
    ToolDefinition,
    tool_registry,
)
from .factory import (
    ToolFactory,
    ToolConfig,
    ToolType,
)
from .base import BaseTool, ToolMetadata

# Import defaults to auto-register factory functions
from . import defaults as _defaults  # noqa: F401

__all__ = [
    # Registry
    'ToolRegistry',
    'ToolDefinition',
    'tool_registry',
    # Factory
    'ToolFactory',
    'ToolConfig',
    'ToolType',
    # Base
    'BaseTool',
    'ToolMetadata',
]

