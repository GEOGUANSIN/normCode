"""
Core package for NPC Normative Plan in Concepts.
This package provides the core functionality for concept-based normative planning.
"""

__version__ = "0.1.0"

# Import main components for easier access
from ._agentframe import AgentFrame
from ._npc_components import Plan
from ._conceptualizers import DOTParser

__all__ = [
    'AgentFrame',
    'Plan',
    'DOTParser',
] 