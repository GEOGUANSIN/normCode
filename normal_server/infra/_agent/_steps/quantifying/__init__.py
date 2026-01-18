"""
This file initializes the 'quantifying' steps package.
"""

from infra._agent._steps.quantifying import _iwi as quantifying_iwi
from infra._agent._steps.quantifying import _ir as quantifying_ir
from infra._agent._steps.quantifying import _gr as quantifying_gr
from infra._agent._steps.quantifying import _qr as quantifying_qr
from infra._agent._steps.quantifying import _or as quantifying_or
from infra._agent._steps.quantifying import _owi as quantifying_owi 

quantifying_methods = {
    "input_working_interpretation": quantifying_iwi.input_working_interpretation,
    "input_references": quantifying_ir.input_references,
    "grouping_references": quantifying_gr.grouping_references,
    "quantifying_references": quantifying_qr.quantifying_references,
    "output_reference": quantifying_or.output_reference,
    "output_working_interpretation": quantifying_owi.output_working_interpretation,
}


__all__ = [
    "quantifying_iwi",
    "quantifying_ir",
    "quantifying_gr",
    "quantifying_qr",
    "quantifying_or",
    "quantifying_owi",
    "quantifying_methods"
]