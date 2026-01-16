"""
This file initializes the 'judgement_in_composition' steps package.
"""

from . import _iwi as judgement_iwi
from . import _ir as judgement_ir
from . import _mfp as judgement_mfp
from . import _mvp as judgement_mvp
from . import _tva as judgement_tva
from . import _tia as judgement_tia
from . import _or as judgement_or
from . import _owi as judgement_owi

judgement_in_composition_methods = {
    "input_working_interpretation": judgement_iwi.input_working_interpretation,
    "input_references": judgement_ir.input_references,
    "model_function_perception": judgement_mfp.model_function_perception,
    "memory_value_perception": judgement_mvp.memory_value_perception,
    "tool_value_actuation": judgement_tva.tool_value_actuation,
    "truth_inference_assertion": judgement_tia.truth_inference_assertion,
    "output_reference": judgement_or.output_reference,
    "output_working_interpretation": judgement_owi.output_working_interpretation,
}


__all__ = [
    "judgement_iwi",
    "judgement_ir",
    "judgement_mfp",
    "judgement_mvp",
    "judgement_tva",
    "judgement_tia",
    "judgement_or",
    "judgement_owi",
    "judgement_in_composition_methods"
]
