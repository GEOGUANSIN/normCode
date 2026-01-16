"""
This file initializes the 'simple' steps package.
"""

from infra._agent._steps.simple import _iwi as simple_iwi
from infra._agent._steps.simple import _ir as simple_ir
from infra._agent._steps.simple import _or as simple_or
from infra._agent._steps.simple import _owi as simple_owi 


simple_methods = {
    "input_working_interpretation": simple_iwi.input_working_interpretation,
    "input_references": simple_ir.input_references,
    "output_reference": simple_or.output_reference,
    "output_working_interpretation": simple_owi.output_working_interpretation,
}


__all__ = [
    "simple_iwi",
    "simple_ir",
    "simple_or",
    "simple_owi",
    "simple_methods"
]