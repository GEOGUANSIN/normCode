from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class BaseSyntax(BaseModel):
    type: str
    model_config = ConfigDict(arbitrary_types_allowed=True)

class GroupingSyntax(BaseSyntax):
    """Syntax for grouping (e.g., &in, &across)."""
    marker: Optional[Literal["in", "across", "only"]] = None
    by_axes: Optional[Any] = None
    annotation_list: Optional[List[str]] = None
    template: Optional[Any] = None

class QuantifyingSyntax(BaseSyntax):
    """Syntax for quantifying (e.g., *every)."""
    loop_base_concept_name: Optional[str] = None
    view_axes: List[str] = Field(default_factory=list)
    concept_to_infer: List[str] = Field(default_factory=list)
    loop_index: Optional[int] = None
    carry: Optional[Dict[str, int]] = None

class ImperativeSyntax(BaseSyntax):
    """Syntax for imperative (::) forms."""
    value_order: Optional[Any] = None

# Allow legacy dicts for backward compatibility
SyntaxUnion = Union[GroupingSyntax, QuantifyingSyntax, ImperativeSyntax, Dict[str, Any]]

__all__ = [
    "BaseSyntax",
    "GroupingSyntax",
    "QuantifyingSyntax",
    "ImperativeSyntax",
    "SyntaxUnion",
] 