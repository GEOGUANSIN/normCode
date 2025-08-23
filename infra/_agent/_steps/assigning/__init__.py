"""
This file initializes the 'assigning' steps package.
"""

from infra._agent._steps.assigning import _iwi as assigning_iwi
from infra._agent._steps.assigning import _ir as assigning_ir
from infra._agent._steps.assigning import _ar as assigning_ar
from infra._agent._steps.assigning import _or as assigning_or
from infra._agent._steps.assigning import _owi as assigning_owi


assigning_methods = {
    "input_working_interpretation": assigning_iwi.input_working_interpretation,
    "input_references": assigning_ir.input_references,
    "assigning_references": assigning_ar.assigning_references,
    "output_reference": assigning_or.output_reference,
    "output_working_interpretation": assigning_owi.output_working_interpretation,
}


__all__ = [
    "assigning_iwi",
    "assigning_ir",
    "assigning_ar",
    "assigning_or",
    "assigning_owi",
    "assigning_methods"
] 