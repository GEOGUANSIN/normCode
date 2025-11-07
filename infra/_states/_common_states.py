from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from infra._core._reference import Reference
from infra._core._concept import Concept


@dataclass
class SequenceStepSpecLite:
	step_name: str
	step_index: int | None = None


@dataclass
class SequenceSpecLite:
	sequence: List[SequenceStepSpecLite] = field(default_factory=list)
	current_step: str = "IWI"


@dataclass
class ConceptInfoLite:
	id: str | None
	name: str | None
	type: str | None
	context: str | None
	axis_name: str | None = None
	natural_name: str | None = None


@dataclass
class ReferenceRecordLite:
	"""Unified reference record usable for function/values/context/inference."""
	step_name: str
	concept: ConceptInfoLite | None = None
	reference: Reference | None = None
	model: Dict[str, Any] | None = None


class BaseStates:
	"""Base state container for sequences."""
	def __init__(self) -> None:
		self.sequence_state = SequenceSpecLite()
		self.function: List[ReferenceRecordLite] = []
		self.values: List[ReferenceRecordLite] = []
		self.context: List[ReferenceRecordLite] = []
		self.inference: List[ReferenceRecordLite] = []

	def set_current_step(self, name: str) -> None:
		self.sequence_state.current_step = name

	def get_reference(self, category: str, step_name: str) -> Reference | None:
		"""Helper to get a reference from a specific category and step."""
		cat_list = getattr(self, category, [])
		for record in cat_list:
			if record.step_name == step_name:
				return record.reference
		return None

	def get_first_record(self, category: str, step_name: str) -> Optional[ReferenceRecordLite]:
		"""Gets the first record from a category matching the step name."""
		cat_list = getattr(self, category, [])
		for record in cat_list:
			if record.step_name == step_name:
				return record
		return None

	def set_reference(self, category: str, step_name: str, ref: Reference) -> None:
		"""Helper to set a reference in a specific category and step."""
		cat_list = getattr(self, category, [])
		for record in cat_list:
			if record.step_name == step_name:
				record.reference = ref.copy()
				return
		# If not found, append a new record
		cat_list.append(ReferenceRecordLite(step_name=step_name, reference=ref.copy())) 



