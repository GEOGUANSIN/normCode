"""
Methods module for NormCode processing.

This module provides core methods for concept processing, perception, and actuation
in the NormCode framework.
"""

from ._demo import (
    strip_element_wrapper,
    wrap_element_wrapper,
    input_working_configurations,
    output_working_configurations,
    memorized_values_perception,
    actuator_perception,
    on_perception_tool_actuation,
    action_specification_perception,
    memory_actuation,
    return_reference,
    all_demo_methods
)
from ._workspace_demo import (
    all_workspace_demo_methods
)
from ._grouping_demo import (
    all_grouping_demo_methods
)
from ._demo_improved import (
    all_demo_methods_improved
)
__all__ = [
    "strip_element_wrapper",
    "wrap_element_wrapper", 
    "input_working_configurations",
    "output_working_configurations",
    "memorized_values_perception",
    "actuator_perception",
    "on_perception_tool_actuation",
    "action_specification_perception",
    "memory_actuation",
    "return_reference",
    "all_demo_methods",
    "all_workspace_demo_methods",
    "all_grouping_demo_methods"
]
