"""
NormCode Models Module

This module provides language model integration and execution capabilities for the NormCode framework.
It includes LLM clients, prompt management, model sequence execution, and related utilities for
building intelligent agent systems with language model capabilities.
"""

# Core model classes
from ._language_models import LanguageModel
from ._model_runner import ModelEnv, ModelSequenceRunner
from ._prompt import PromptTool

# Model state dataclasses (from _states for convenience)
from infra._states._model_state import (
    AffordanceSpecLite,
    ToolSpecLite,
    ModelEnvSpecLite,
    ModelStepSpecLite,
    ModelSequenceSpecLite,
    MetaValue,
    AffordanceValue,
)

# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Models Framework - Language model integration and execution"

# Public API
__all__ = [
    # Core classes
    "LanguageModel",
    "ModelEnv",
    "ModelSequenceRunner",
    "PromptTool",
    
    # Model state dataclasses
    "AffordanceSpecLite",
    "ToolSpecLite",
    "ModelEnvSpecLite",
    "ModelStepSpecLite",
    "ModelSequenceSpecLite",
    "MetaValue",
    "AffordanceValue",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
]
