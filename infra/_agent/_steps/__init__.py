"""
NormCode Steps Module

This module provides step implementations for different inference sequences in the NormCode framework.
It includes step modules for simple, imperative, grouping, and quantifying sequences.
"""

# Import all step modules
from infra._agent._steps import simple
from infra._agent._steps import imperative
from infra._agent._steps import grouping
from infra._agent._steps import quantifying

# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Steps Framework - Step implementations for inference sequences"

# Public API
__all__ = [
    # Step modules
    "simple",
    "imperative", 
    "grouping",
    "quantifying",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
]
