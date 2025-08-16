from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from .types import StepLiteral
from .concept import ConceptInfo
from .model import ModelSpec
from .tools import ToolSpec
from .specs import MemorySpec

class StepReference(BaseModel):
    """Common fields shared by step reference blocks."""

    step_name: StepLiteral
    step_index: Optional[int] = Field(default=None, ge=1)

    # Concept information
    concept: Optional[ConceptInfo] = None

    # May hold a `Reference` or any other value; leave as Any for flexibility.
    reference: Optional[Any] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

class FunctionReference(StepReference):
    """Reference to function-related steps. Typically used for MFP."""

    # Could be list or mapping depending on the use case; keep flexible.
    value_order: Optional[Union[List[str], Dict[str, int]]] = None
    model: Optional[ModelSpec] = None

class ValuesReference(StepReference):
    """Reference to value-oriented steps (e.g., TVA, MVP, IR)."""

    extraction: Optional[str] = None
    quantification: Optional[str] = None
    value_order: Optional[List[str]] = None
    cross_values: Optional[Any] = None
    memory: Optional[MemorySpec] = None

class ContextReference(StepReference):
    """Reference to context entries (often used with IR)."""

    extraction: Optional[str] = None
    quantification: Optional[str] = None

class InferenceReference(StepReference):
    """Reference to inference-related steps (e.g., TIP, MIA)."""

    extraction: Optional[str] = None
    quantification: Optional[str] = None
    tools: List[ToolSpec] = Field(default_factory=list)

class StepReferenceAccessor(list):
    """List-like accessor providing convenience properties over step references.

    - `.reference` returns the list of references from the earliest step(s)
      that contain a non-None reference.
    - `.concept` returns the list of concepts from the earliest step(s)
      that contain a non-None concept.
    - Any other attribute access `.<attr>` will attempt to collect values of
      `<attr>` from the earliest step(s) that provide a non-None value.
    """

    def _collect_at_earliest(self, attribute_name: str) -> List[Any]:
        # Filter items that have both a step_index and a non-None attribute value
        eligible = [
            item
            for item in self
            if getattr(item, attribute_name, None) is not None
            and getattr(item, "step_index", None) is not None
        ]
        if not eligible:
            return []
        earliest_index = min(
            item.step_index for item in eligible if getattr(item, "step_index", None) is not None
        )
        return [
            getattr(item, attribute_name)
            for item in self
            if getattr(item, "step_index", None) == earliest_index
            and getattr(item, attribute_name, None) is not None
        ]

    @property
    def reference(self) -> List[Any]:
        return self._collect_at_earliest("reference")

    @property
    def concept(self) -> List[Any]:
        return self._collect_at_earliest("concept")

    def __getattr__(self, name: str) -> Any:
        # Defer to list's attributes when present
        try:
            return super().__getattribute__(name)
        except AttributeError:
            # Attempt to collect values for arbitrary attributes across items
            return self._collect_at_earliest(name)

__all__ = [
    "StepReferenceAccessor",
    "StepReference",
    "FunctionReference",
    "ValuesReference",
    "ContextReference",
    "InferenceReference",
] 