from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, model_validator

class ConceptInfo(BaseModel):
    """Core information about a Concept, focusing on essential attributes."""

    id: str
    name: str
    type: str
    context: str = ""
    axis_name: Optional[str] = None

    @model_validator(mode="after")
    def _set_default_axis_name(self) -> "ConceptInfo":
        if self.axis_name is None:
            self.axis_name = self.name
        return self

__all__ = ["ConceptInfo"] 