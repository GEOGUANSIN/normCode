"""
NormCode New NP Module

This module provides the core components for the NormCode system's new NP (Neural Processing) framework.
It includes concepts, references, inference mechanisms, and related utilities for building
intelligent agent systems with formal reasoning capabilities.
"""

# Core classes
from ._concept import Concept, CONCEPT_TYPES
from ._reference import Reference, cross_product, cross_action, element_action
from ._inference import Inference
from ._agentframe import AgentFrame, strip_element_wrapper, wrap_element_wrapper
from ._language_models import LanguageModel

# Type classification constants
from ._concept import (
    TYPE_CLASS_SYNTACTICAL,
    TYPE_CLASS_SEMANTICAL, 
    TYPE_CLASS_INFERENTIAL
)

# Concept type constants
from ._concept import CONCEPT_TYPES

# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode New NP Framework - Core components for intelligent agent systems"

# Public API
__all__ = [
    # Core classes
    "Concept",
    "Reference", 
    "Inference",
    "AgentFrame",
    "LanguageModel",
    
    # Functions
    "cross_product",
    "cross_action", 
    "element_action",
    "strip_element_wrapper",
    "wrap_element_wrapper",
    
    # Constants
    "CONCEPT_TYPES",
    "TYPE_CLASS_SYNTACTICAL",
    "TYPE_CLASS_SEMANTICAL",
    "TYPE_CLASS_INFERENTIAL",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
]
