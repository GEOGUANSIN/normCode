"""
This file initializes the 'grouping' steps package.
"""

from infra._agent._steps.grouping import _iwi as grouping_iwi
from infra._agent._steps.grouping import _ir as grouping_ir
from infra._agent._steps.grouping import _gr as grouping_gr
from infra._agent._steps.grouping import _or as grouping_or
from infra._agent._steps.grouping import _owi as grouping_owi 


__all__ = [
    "grouping_iwi",
    "grouping_ir",
    "grouping_gr",
    "grouping_or",
    "grouping_owi"
]