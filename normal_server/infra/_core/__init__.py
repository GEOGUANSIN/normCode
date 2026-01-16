"""
NormCode Core Module

This module provides the core components for the NormCode system's NP (Normal Plan) framework.
It includes concepts, references, inference mechanisms, and related utilities for building
intelligent agent systems with formal reasoning capabilities.
"""

# Core classes
from ._concept import Concept, CONCEPT_TYPES, TYPE_CLASS_SYNTACTICAL, TYPE_CLASS_SEMANTICAL, TYPE_CLASS_INFERENTIAL
from ._reference import Reference, cross_product, cross_action, element_action, join, set_dev_mode, get_dev_mode
from ._inference import Inference, register_inference_sequence


# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Core Framework - Core components for intelligent agent systems"

# Public API
__all__ = [
    # Core classes
    "Concept",
    "Reference", 
    "Inference",
    
    # Functions
    "cross_product",
    "cross_action", 
    "element_action",
    "join",
    "register_inference_sequence",
    
    # Dev mode utilities
    "set_dev_mode",
    "get_dev_mode",
    
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
