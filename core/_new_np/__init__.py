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
from ._agentframe import AgentFrame

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
    
    # Functions
    "cross_product",
    "cross_action", 
    "element_action",
    
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

# Convenience imports for common use cases
def create_concept(name: str, context: str = "", reference=None, concept_type: str = "{}") -> Concept:
    """
    Convenience function to create a Concept instance.
    
    Args:
        name: The name of the concept
        context: The context string
        reference: Optional Reference instance
        concept_type: The concept type (default: "{}" for object)
    
    Returns:
        Concept: A new Concept instance
    """
    return Concept(name, context, reference, concept_type)

def create_reference(axes: list[str], shape: tuple[int, ...], initial_value=None) -> Reference:
    """
    Convenience function to create a Reference instance.
    
    Args:
        axes: List of axis names
        shape: Tuple of dimensions for each axis
        initial_value: Initial value for all elements (default: None)
    
    Returns:
        Reference: A new Reference instance
    """
    return Reference(axes, shape, initial_value)

def create_inference(sequence_name: str, concept_to_infer: Concept, 
                    value_concepts: list[Concept], function_concept: Concept) -> Inference:
    """
    Convenience function to create an Inference instance.
    
    Args:
        sequence_name: Name of the inference sequence
        concept_to_infer: Concept to infer
        value_concepts: List of value concepts
        function_concept: Function concept
    
    Returns:
        Inference: A new Inference instance
    """
    return Inference(sequence_name, concept_to_infer, value_concepts, function_concept)

# Add convenience functions to __all__
__all__.extend([
    "create_concept",
    "create_reference", 
    "create_inference"
])
