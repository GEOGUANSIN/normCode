"""
NormCode States Module

This module provides state management classes for different inference sequences in the NormCode framework.
It includes base state classes and specific state implementations for simple, imperative, grouping, quantifying, and assigning sequences.
"""

# Import state classes with correct file names
from ._common_states import BaseStates, SequenceStepSpecLite, SequenceSpecLite, ConceptInfoLite, ReferenceRecordLite
from ._simple_states import States as SimpleStates
from ._imperative_states import States as ImperativeStates
from ._grouping_states import States as GroupingStates
from ._quantifying_states import States as QuantifyingStates
from ._assigning_states import States as AssigningStates
from ._timing_states import States as TimingStates
from ._model_state import (
    AffordanceSpecLite, ToolSpecLite, ModelEnvSpecLite, ModelStepSpecLite,
    ModelSequenceSpecLite, MetaValue, AffordanceValue
)

# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode States Framework - State management for inference sequences"

# Public API
__all__ = [
    # Base state classes
    "BaseStates",
    "SequenceStepSpecLite", 
    "SequenceSpecLite",
    "ConceptInfoLite",
    "ReferenceRecordLite",
    
    # Sequence-specific state classes
    "SimpleStates",
    "ImperativeStates",
    "GroupingStates", 
    "QuantifyingStates",
    "AssigningStates",
    "TimingStates",
    
    # Model state dataclasses
    "AffordanceSpecLite",
    "ToolSpecLite",
    "ModelEnvSpecLite",
    "ModelStepSpecLite",
    "ModelSequenceSpecLite",
    "MetaValue",
    "AffordanceValue",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
] 