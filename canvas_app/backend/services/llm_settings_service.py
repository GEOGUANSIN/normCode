"""
LLM Settings Service - Manages LLM provider configurations.

This module provides backward-compatible exports from the refactored
agent sub-package. The implementation has been moved to:

- services/agent/llm_providers.py - LLMSettingsService

This file is a facade that re-exports the public API for backward
compatibility with existing code.

Configuration is stored in:
- Primary: canvas_app/backend/tools/llm-settings.json (same dir as llm_tool.py)
- Also exports to settings.yaml for compatibility with legacy code
"""

# Re-export from the agent sub-package
from services.agent import (
    LLMSettingsService,
    llm_settings_service,
)

__all__ = [
    'LLMSettingsService',
    'llm_settings_service',
]
