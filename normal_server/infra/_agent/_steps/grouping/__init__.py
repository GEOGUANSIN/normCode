"""
This file initializes the 'grouping' steps package.
"""

from infra._agent._steps.grouping import _iwi as grouping_iwi
from infra._agent._steps.grouping import _ir as grouping_ir
from infra._agent._steps.grouping import _gr as grouping_gr
from infra._agent._steps.grouping import _or as grouping_or
from infra._agent._steps.grouping import _owi as grouping_owi 


grouping_methods = {
    "input_working_interpretation": grouping_iwi.input_working_interpretation,
    "input_references": grouping_ir.input_references,
    "grouping_references": grouping_gr.grouping_references,
    "output_reference": grouping_or.output_reference,
    "output_working_interpretation": grouping_owi.output_working_interpretation,
}


__all__ = [
    "grouping_iwi",
    "grouping_ir",
    "grouping_gr",
    "grouping_or",
    "grouping_owi",
    "grouping_methods"
]