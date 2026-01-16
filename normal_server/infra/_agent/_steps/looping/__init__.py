"""
This file initializes the 'looping' steps package.
"""

from infra._agent._steps.looping import _iwi as looping_iwi
from infra._agent._steps.looping import _ir as looping_ir
from infra._agent._steps.looping import _gr as looping_gr
from infra._agent._steps.looping import _lr as looping_lr
from infra._agent._steps.looping import _or as looping_or
from infra._agent._steps.looping import _owi as looping_owi 

looping_methods = {
    "input_working_interpretation": looping_iwi.input_working_interpretation,
    "input_references": looping_ir.input_references,
    "grouping_references": looping_gr.grouping_references,
    "looping_references": looping_lr.looping_references,
    "output_reference": looping_or.output_reference,
    "output_working_interpretation": looping_owi.output_working_interpretation,
}


__all__ = [
    "looping_iwi",
    "looping_ir",
    "looping_gr",
    "looping_lr",
    "looping_or",
    "looping_owi",
    "looping_methods"
]
