"""
NormCode Orchestration Module

This module provides orchestration capabilities for the NormCode framework.
It includes parsers for NormCode expressions and blackboard management.
"""

# Parser functions
from infra._orchest._parser import (
    _parse_normcode_grouping,
    _parse_normcode_quantifying,
    _parse_normcode_assigning,
    _parse_normcode_timing
)

# Core classes
from infra._orchest._blackboard import Blackboard

# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Orchestration Framework - Parsing and blackboard management"

# Public API
__all__ = [
    # Parser functions
    "_parse_normcode_grouping",
    "_parse_normcode_quantifying", 
    "_parse_normcode_assigning",
    "_parse_normcode_timing",
    
    # Core classes
    "Blackboard",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
] 