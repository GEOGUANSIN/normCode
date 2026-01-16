"""
This file initializes the 'judgement_direct' steps package.
"""

from infra._agent._steps.judgement_direct import _iwi as judgement_iwi
from infra._agent._steps.judgement_direct import _ir as judgement_ir
from infra._agent._steps.judgement_direct import _mfp as judgement_mfp
from infra._agent._steps.judgement_direct import _mvp as judgement_mvp
from infra._agent._steps.judgement_direct import _tva as judgement_tva
from infra._agent._steps.judgement_direct import _tip as judgement_tip
from infra._agent._steps.judgement_direct import _mia as judgement_mia
from infra._agent._steps.judgement_direct import _or as judgement_or
from infra._agent._steps.judgement_direct import _owi as judgement_owi

judgement_direct_methods = {
    "input_working_interpretation": judgement_iwi.input_working_interpretation,
    "input_references": judgement_ir.input_references,
    "model_function_perception": judgement_mfp.model_function_perception,
    "memory_value_perception": judgement_mvp.memory_value_perception,
    "tool_value_actuation": judgement_tva.tool_value_actuation,
    "tool_inference_perception": judgement_tip.tool_inference_perception,
    "memory_inference_actuation": judgement_mia.memory_inference_actuation,
    "output_reference": judgement_or.output_reference,
    "output_working_interpretation": judgement_owi.output_working_interpretation,
}


__all__ = [
    "judgement_iwi",
    "judgement_ir",
    "judgement_mfp",
    "judgement_mvp",
    "judgement_tva",
    "judgement_tip",
    "judgement_mia",
    "judgement_or",
    "judgement_owi",
    "judgement_direct_methods"
]
