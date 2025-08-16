from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel


class MemorySpec(BaseModel):
	"""Memory configuration spec for value steps."""

	type: str
	# Optional fields per example usage
	value_order: Optional[Any] = None
	cross_values: Optional[bool] = None


__all__ = ["MemorySpec"] 