"""
NormCode Agent Module

This module provides agent framework capabilities for the NormCode system.
It includes the AgentFrame class for managing and configuring inference sequences,
along with utility functions for element wrapping and logging setup.
It also includes step implementations and model integration capabilities.
"""

# Core agent classes
from infra._agent._agentframe import AgentFrame
from infra._agent._body import Body

# Utility functions
from infra._agent._agentframe import (
    strip_element_wrapper,
    wrap_element_wrapper,
    setup_logging
)

# Import step modules
from infra._agent import _steps
from infra._agent import _models
from infra._agent import _sequences

# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Agent Framework - Agent management, steps, and model integration"

# Public API
__all__ = [
    # Core classes
    "AgentFrame",
    "Body",
    
    # Utility functions
    "strip_element_wrapper",
    "wrap_element_wrapper",
    "setup_logging",
    
    # Step modules
    "_steps",
    
    # Model classes
    "_models",

    # Sequence modules
    "_sequences",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
]
