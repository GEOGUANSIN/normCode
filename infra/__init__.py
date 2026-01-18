"""
NormCode Infrastructure Module

This module provides the complete infrastructure for the NormCode system's NP (Normal Plan) framework.
It includes core components, agent framework, state management, syntax processing, and model integration
for building intelligent agent systems with formal reasoning capabilities.
"""

# ============================================================================
# Windows Console UTF-8 Encoding Fix
# ============================================================================
# On Windows, the console defaults to cp1252 encoding which can't handle Chinese
# and other Unicode characters. This fix must run before any print() or logging
# calls to ensure proper encoding support.
import sys

def _configure_utf8_console():
    """
    Configure Windows console for UTF-8 encoding.
    
    This fixes 'UnicodeEncodeError' when printing Chinese or other non-ASCII
    characters to the Windows console. Uses 'replace' error handling to
    substitute unencodable characters instead of crashing.
    
    Uses reconfigure() method (Python 3.7+) which is the safe way to change
    encoding without replacing the stream object.
    """
    if sys.platform == "win32":
        try:
            # Use reconfigure() to safely change encoding without replacing streams
            # This avoids "I/O operation on closed file" errors
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # Silently ignore if configuration fails (e.g., in some IDEs or
            # when stdout/stderr are not standard streams)
            pass

# Apply UTF-8 encoding fix on module import
_configure_utf8_console()

# ============================================================================

# Core components
from infra._core import (
    Concept, Reference, Inference,
    cross_product, cross_action, element_action, join,
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
    "join",
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
