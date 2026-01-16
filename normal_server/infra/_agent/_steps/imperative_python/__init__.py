"""
This file initializes the 'imperative_python' steps package.
"""

from infra._agent._steps.imperative_python import _iwi as imperative_iwi
from infra._agent._steps.imperative_python import _ir as imperative_ir
from infra._agent._steps.imperative_python import _mfp as imperative_mfp
from infra._agent._steps.imperative_python import _mvp as imperative_mvp
from infra._agent._steps.imperative_python import _tva as imperative_tva
from infra._agent._steps.imperative_python import _tip as imperative_tip
from infra._agent._steps.imperative_python import _mia as imperative_mia
from infra._agent._steps.imperative_python import _or as imperative_or
from infra._agent._steps.imperative_python import _owi as imperative_owi

imperative_python_methods = {
    "input_working_interpretation": imperative_iwi.input_working_interpretation,
    "input_references": imperative_ir.input_references,
    "model_function_perception": imperative_mfp.model_function_perception,
    "memory_value_perception": imperative_mvp.memory_value_perception,
    "tool_value_actuation": imperative_tva.tool_value_actuation,
    "tool_inference_perception": imperative_tip.tool_inference_perception,
    "memory_inference_actuation": imperative_mia.memory_inference_actuation,
    "output_reference": imperative_or.output_reference,
    "output_working_interpretation": imperative_owi.output_working_interpretation,
}


__all__ = [
    "imperative_iwi",
    "imperative_ir",
    "imperative_mfp",
    "imperative_mvp",
    "imperative_tva",
    "imperative_tip",
    "imperative_mia",
    "imperative_or",
    "imperative_owi",
    "imperative_python_methods"
] 