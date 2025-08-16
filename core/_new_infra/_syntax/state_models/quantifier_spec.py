from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class QuantifierSpec(BaseModel):
	"""Specification for quantification behavior in value/inference steps."""

	type: str
	loop_base_concept_name: Optional[str] = None
	mode: Optional[str] = None
	start_index: Optional[int] = 0
	carry_index: Optional[int] = 0


__all__ = ["QuantifierSpec"] 