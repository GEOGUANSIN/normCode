"""
This file initializes the 'timing' steps package.
"""

from infra._agent._steps.timing import _iwi as timing_iwi
from infra._agent._steps.timing import _t as timing_t
from infra._agent._steps.timing import _owi as timing_owi


timing_methods = {
    "input_working_interpretation": timing_iwi.input_working_interpretation,
    "timing": timing_t.timing,
    "output_working_interpretation": timing_owi.output_working_interpretation,
}


__all__ = [
    "timing_iwi",
    "timing_t",
    "timing_owi",
    "timing_methods"
] 