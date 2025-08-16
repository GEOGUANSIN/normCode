from __future__ import annotations
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ToolSpec(BaseModel):
    """Static definition of a tool and its affordances.

    affordances: list of AffordanceSpec entries describing available affordances.
    Each affordance may omit params for static definition.
    """

    tool_name: str
    affordances: List["AffordanceSpec"] = Field(default_factory=list)

class AffordanceSpec(BaseModel):
    """Runtime binding of a tool affordance to concrete parameters (ready to execute).
    """

    affordance_name: str
    params: Dict[str, Any] = Field(default_factory=dict)  # e.g., {"value": "123"}
    call_code: str = Field(default="")  # e.g., "result = something.read(**params)"
    output: Optional[str] = Field(default="result")  # variable to read after exec statements; defaults to "result"

__all__ = ["ToolSpec", "AffordanceSpec"]

# Resolve forward references for Pydantic v2
ToolSpec.model_rebuild()
AffordanceSpec.model_rebuild() 