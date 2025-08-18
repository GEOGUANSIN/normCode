"""
NormCode Syntax Module

This module provides syntax parsing and processing capabilities for the NormCode framework.
It includes parsers for NormCode expressions, grouping operations, and quantification processing.
"""

# Core syntax classes
from infra._syntax._parser import GrouperInfo
from infra._syntax._grouper import Grouper
from infra._syntax._quantifier import Quantifier

# Parser functions
from infra._syntax._parser import (
    _parse_normcode_grouping,
    _parse_normcode_quantifying
)

# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Syntax Framework - Parsing and processing for NormCode expressions"

# Public API
__all__ = [
    # Core classes
    "GrouperInfo",
    "Grouper",
    "Quantifier",
    
    # Parser functions
    "_parse_normcode_grouping",
    "_parse_normcode_quantifying",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
] 