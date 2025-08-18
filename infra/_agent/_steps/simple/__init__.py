"""
This file initializes the 'simple' steps package.
"""

from infra._agent._steps.simple import _iwi as simple_iwi
from infra._agent._steps.simple import _ir as simple_ir
from infra._agent._steps.simple import _or as simple_or
from infra._agent._steps.simple import _owi as simple_owi 


__all__ = [
    "simple_iwi",
    "simple_ir",
    "simple_or",
    "simple_owi"
]