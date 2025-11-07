"""
NormCode Orchestration Module

This module provides orchestration capabilities for the NormCode framework.
It includes parsers for NormCode expressions, blackboard management, and complete orchestration system.
"""

# Parser functions
from infra._orchest._parser import (
    _parse_normcode_grouping,
    _parse_normcode_quantifying,
    _parse_normcode_assigning,
    _parse_normcode_timing
)

# Core orchestration classes
from infra._orchest._blackboard import Blackboard
from infra._orchest._orchestrator import Orchestrator
from infra._orchest._tracker import ProcessTracker

# Data classes and repositories
from infra._orchest._repo import (
    ConceptEntry,
    InferenceEntry,
    ConceptRepo,
    InferenceRepo
)

# Waitlist management
from infra._orchest._waitlist import (
    WaitlistItem,
    Waitlist
)

# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Orchestration Framework - Complete orchestration system with parsing, blackboard management, and workflow execution"

# Public API
__all__ = [
    # Parser functions
    "_parse_normcode_grouping",
    "_parse_normcode_quantifying", 
    "_parse_normcode_assigning",
    "_parse_normcode_timing",
    
    # Core orchestration classes
    "Blackboard",
    "Orchestrator",
    "ProcessTracker",
    
    # Data classes and repositories
    "ConceptEntry",
    "InferenceEntry", 
    "ConceptRepo",
    "InferenceRepo",
    
    # Waitlist management
    "WaitlistItem",
    "Waitlist",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
] 