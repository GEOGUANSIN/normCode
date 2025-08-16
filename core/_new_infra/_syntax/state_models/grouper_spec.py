from __future__ import annotations
from typing import Any, List, Optional
from typing import Literal
from pydantic import BaseModel


class GrouperSpec(BaseModel):
	"""Specification for grouping behavior such as AND IN / OR ACROSS patterns."""

	type: str
	group_marker: Optional[Literal["in", "across", "only"]] = None
	by_axes: Optional[Any] = None
	annotation_list: Optional[List[str]] = None
	template: Optional[Any] = None


__all__ = ["GrouperSpec"] 