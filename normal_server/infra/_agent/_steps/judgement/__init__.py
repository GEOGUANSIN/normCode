"""
This file initializes the 'judgement' steps package.
"""

from infra._agent._steps.judgement._ir import input_references
from infra._agent._steps.judgement._iwi import input_working_interpretation
from infra._agent._steps.judgement._or import output_reference
from infra._agent._steps.judgement._owi import output_working_interpretation
from infra._agent._steps.judgement._mfp import model_function_perception
from infra._agent._steps.judgement._mia import memory_inference_actuation
from infra._agent._steps.judgement._mvp import memory_value_perception
from infra._agent._steps.judgement._tip import tool_inference_perception
from infra._agent._steps.judgement._tva import tool_value_actuation

judgement_methods = {
    "input_working_interpretation": input_working_interpretation,
    "input_references": input_references,
    "model_function_perception": model_function_perception,
    "memory_value_perception": memory_value_perception,
    "tool_value_actuation": tool_value_actuation,
    "tool_inference_perception": tool_inference_perception,
    "memory_inference_actuation": memory_inference_actuation,
    "output_reference": output_reference,
    "output_working_interpretation": output_working_interpretation,
}

__all__ = [
    "input_references",
    "input_working_interpretation",
    "output_reference",
    "output_working_interpretation",
    "model_function_perception",
    "memory_inference_actuation",
    "memory_value_perception",
    "tool_inference_perception",
    "tool_value_actuation",
    "judgement_methods"
] 