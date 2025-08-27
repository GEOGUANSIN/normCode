"""
NormCode Syntax Module

This module provides syntax processing capabilities for the NormCode framework.
It includes syntax classes for grouping operations, quantification processing, assignment operations, and timing.
"""

# Core syntax classes
from infra._syntax._grouper import Grouper
from infra._syntax._quantifier import Quantifier
from infra._syntax._assigner import Assigner
from infra._syntax._timer import Timer



# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Syntax Framework - Parsing and processing for NormCode expressions"

# Public API
__all__ = [
    # Core classes
    "Grouper",
    "Quantifier",
    "Assigner",
    "Timer",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
] 