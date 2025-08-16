from __future__ import annotations
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, model_validator
from .types import StepLiteral

class StepDescriptor(BaseModel):
    """Basic descriptor for a step in the sequence."""

    step_name: StepLiteral
    step_index: Optional[int] = Field(default=None, ge=1)

class AgentSequenceState(BaseModel):
    """Tracks the overall sequence and current execution pointer."""

    sequence: List[StepDescriptor]
    current_step: StepLiteral
    current_step_index: Optional[int] = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _populate_indices(self) -> "AgentSequenceState":
        # Assign step_index to sequence entries if missing based on order (1-based)
        for idx, step in enumerate(self.sequence, start=1):
            if step.step_index is None:
                step.step_index = idx
        # Populate current_step_index if not provided
        if self.current_step_index is None:
            for step in self.sequence:
                if step.step_name == self.current_step:
                    self.current_step_index = step.step_index
                    break
        return self

__all__ = ["StepDescriptor", "AgentSequenceState"] 