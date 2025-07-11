"""
NPC Components package for NPC Normative Plan in Concepts.
This package provides core components for normative planning and concept processing.
"""

from ._plan import Plan
from ._inference import Inference
from ._utils import (
    _process_input_data,
    _identify_base_concepts,
    _identify_object_base_concepts,
    _set_plan_io_from_base_concepts
)

__all__ = [
    'Plan',
    'Inference',
    '_process_input_data',
    '_identify_base_concepts',
    '_identify_object_base_concepts',
    '_set_plan_io_from_base_concepts',
] 