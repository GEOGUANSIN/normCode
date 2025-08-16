from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict
from .types import StepLiteral
from .sequence import AgentSequenceState
from .syntax_models import SyntaxUnion
from .references import StepReferenceAccessor, FunctionReference, ValuesReference, ContextReference, InferenceReference

class ReferenceInterpretationState(BaseModel):
    """Top-level structure for the working interpretation/state tracker."""

    sequence_state: AgentSequenceState
    # Parsed syntax for current sequence (grouping/quantifying/imperative)
    syntax: Optional[SyntaxUnion] = None
    # Shared mutable workspace for steps (e.g., quantifier subworkspaces)
    workspace: Dict[str, Any] = Field(default_factory=dict)

    # Reference blocks for different aspects of the sequence
    function: List[FunctionReference] = Field(default_factory=list)
    values: List[ValuesReference] = Field(default_factory=list)
    context: List[ContextReference] = Field(default_factory=list)
    inference: List[InferenceReference] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __getattribute__(self, name: str):  # type: ignore[override]
        # Wrap reference blocks with accessor to expose `.reference`
        if name in {"function", "values", "context", "inference"}:
            items = super().__getattribute__(name)
            try:
                # Avoid double-wrapping
                if isinstance(items, StepReferenceAccessor):
                    return items
                return StepReferenceAccessor(items)
            except Exception:
                return items
        return super().__getattribute__(name)

    @model_validator(mode="after")
    def _fill_step_indices_from_sequence(self) -> "ReferenceInterpretationState":
        # Make a map from step_name to index (first occurrence)
        name_to_index: Dict[StepLiteral, int] = {}
        for step in self.sequence_state.sequence:
            if step.step_name not in name_to_index and step.step_index is not None:
                name_to_index[step.step_name] = step.step_index
        # Helper to fill missing indices for a list of StepReference-derived items
        def _populate(items: List[Any]) -> None:
            for item in items:
                if hasattr(item, "step_index") and getattr(item, "step_index") is None:
                    mapped = name_to_index.get(getattr(item, "step_name"))
                    if mapped is not None:
                        item.step_index = mapped
        _populate(self.function)
        _populate(self.values)
        _populate(self.context)
        _populate(self.inference)
        return self

__all__ = ["ReferenceInterpretationState"] 