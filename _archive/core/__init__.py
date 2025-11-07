"""
Core package for NormCode - Neural Processing (NP) Framework.
This package provides the core functionality for concept-based normative planning and intelligent agent systems.
"""

__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Core - Neural Processing Framework for intelligent agent systems"

# Import new NP components (primary focus)
from ._new_np import (
    # Core classes
    Concept,
    Reference,
    Inference,
    AgentFrame,
    
    # Functions
    cross_product,
    cross_action,
    element_action,
    
    # Constants
    CONCEPT_TYPES,
    TYPE_CLASS_SYNTACTICAL,
    TYPE_CLASS_SEMANTICAL,
    TYPE_CLASS_INFERENTIAL,
    
    # Convenience functions
    create_concept,
    create_reference,
    create_inference,
)

# Import legacy components for backward compatibility
from ._agentframe import AgentFrame as LegacyAgentFrame
from ._npc_components import Plan
from ._conceptualizers import DOTParser
from ._language_models import LanguageModel

__all__ = [
    # New NP Framework (Primary)
    'Concept',
    'Reference', 
    'Inference',
    'AgentFrame',
    'cross_product',
    'cross_action',
    'element_action',
    'CONCEPT_TYPES',
    'TYPE_CLASS_SYNTACTICAL',
    'TYPE_CLASS_SEMANTICAL',
    'TYPE_CLASS_INFERENTIAL',
    'create_concept',
    'create_reference',
    'create_inference',
    
    # Legacy components (for backward compatibility)
    'LegacyAgentFrame',
    'Plan',
    'DOTParser',
    'LanguageModel',
    
    # Module info
    '__version__',
    '__author__',
    '__description__',
] 