"""
NormCode Infrastructure Module

This module provides the complete infrastructure for the NormCode system's NP (Normal Plan) framework.
It includes core components, agent framework, state management, syntax processing, and model integration
for building intelligent agent systems with formal reasoning capabilities.
"""

# Core components
from infra._core import (
    Concept, Reference, Inference,
    cross_product, cross_action, element_action,
    CONCEPT_TYPES, TYPE_CLASS_SYNTACTICAL, TYPE_CLASS_SEMANTICAL, TYPE_CLASS_INFERENTIAL,
    register_inference_sequence
)

# Agent framework (includes steps and models)
from infra._agent import (
    AgentFrame, Body, strip_element_wrapper, wrap_element_wrapper, setup_logging, _steps, _models
)

# State management
from infra._states import (
    BaseStates, SequenceStepSpecLite, SequenceSpecLite, ConceptInfoLite, ReferenceRecordLite,
    SimpleStates, ImperativeStates, GroupingStates, QuantifyingStates
)

# Syntax processing
from infra._syntax import (
    Grouper, Quantifier, Assigner, Timer
)

# Orchestration (parsing and blackboard)
from infra._orchest import (
    _parse_normcode_grouping, _parse_normcode_quantifying, _parse_normcode_assigning, _parse_normcode_timing,
    Orchestrator, ProcessTracker, ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, WaitlistItem, Waitlist, Blackboard
)

# Logging
from infra._loggers import (
    log_states_progress,
    _log_concept_details,
    _log_inference_result,
)


# Import submodules for direct access
from infra import _core
from infra import _agent
from infra import _states
from infra import _syntax
from infra import _loggers
from infra import _orchest

# Version and module info
__version__ = "1.0.0"
__author__ = "NormCode Team"
__description__ = "NormCode Infrastructure Framework - Complete system for intelligent agent development"

# Public API
__all__ = [
    # Core classes
    "Concept",
    "Reference", 
    "Inference",
    
    # Core functions
    "cross_product",
    "cross_action", 
    "element_action",
    "register_inference_sequence",
    
    # Core constants
    "CONCEPT_TYPES",
    "TYPE_CLASS_SYNTACTICAL",
    "TYPE_CLASS_SEMANTICAL",
    "TYPE_CLASS_INFERENTIAL",
    
    # Agent framework
    "AgentFrame",
    "Body",
    "strip_element_wrapper",
    "wrap_element_wrapper",
    "setup_logging",

    # Logging
    "log_states_progress",
    "_log_concept_details",
    "_log_inference_result",
    
    # Step modules
    "_steps",
    
    # Model classes
    "_models",
    
    # State management
    "BaseStates", "SequenceStepSpecLite", "SequenceSpecLite", "ConceptInfoLite", "ReferenceRecordLite",
    "SimpleStates", "ImperativeStates", "GroupingStates", "QuantifyingStates",
    
    # Syntax processing
    "Grouper", "Quantifier", "Assigner", "Timer",
    "_parse_normcode_grouping", "_parse_normcode_quantifying", "_parse_normcode_assigning", "_parse_normcode_timing",
    
    # Orchestration
    "Orchestrator",
    "ProcessTracker",
    "ConceptEntry",
    "InferenceEntry",
    "ConceptRepo",
    "InferenceRepo",
    "WaitlistItem",
    "Waitlist",
    "Blackboard",

    # Submodules
    "_core", "_agent", "_states", "_syntax", "_loggers", "_orchest",
    
    # Module info
    "__version__",
    "__author__",
    "__description__"
]
