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

	def set_reference(self, category: str, step_name: str, ref: Reference) -> None:
		"""Helper to set a reference in a specific category and step."""
		cat_list = getattr(self, category, [])
		for record in cat_list:
			if record.step_name == step_name:
				record.reference = ref.copy()
				return
		# If not found, append a new record
		cat_list.append(ReferenceRecordLite(step_name=step_name, reference=ref.copy())) 




def _log_concept_details(concept, reference=None, example_number=None, concept_name=None):
    """Helper function to log concept details in a consistent format"""
    if example_number and concept_name:
        logger.info(f"{example_number}. {concept_name}:")
    
    logger.info(f"   Concept: {concept.name}")
    logger.info(f"   Type: {concept.type} ({concept.get_type_class()})")
    
    if reference and isinstance(reference, Reference):
        # Get all values from the reference using slice(None) for all axes
        slice_params = {axis: slice(None) for axis in reference.axes}
        all_values = reference.get(**slice_params)
        logger.info(f"   All values: {all_values}")
        logger.info(f"   All values without skip values: {reference.get_tensor(ignore_skip=True)}")
        logger.info(f"   Axes: {reference.axes}")

def _log_inference_result(result_concept, value_concepts, function_concept):
    """Log the inference result and related information"""
    if result_concept.reference:
        logger.info(f"Answer concept reference: {result_concept.reference.tensor}")
        logger.info(f"Answer concept reference without skip values: {result_concept.reference.get_tensor(ignore_skip=True)}")
        logger.info(f"Answer concept axes: {result_concept.reference.axes}")
        
        # Create list of all references for cross product
        all_references = [result_concept.reference]
        if value_concepts:
            all_references.extend([concept.reference for concept in value_concepts if concept.reference])
        if function_concept and function_concept.reference:
            all_references.append(function_concept.reference)
        
        if len(all_references) > 1:
            all_info_reference = cross_product(all_references)
            logger.info(f"All info reference: {all_info_reference.tensor}")
            logger.info(f"All info reference without skip values: {all_info_reference.get_tensor(ignore_skip=True)}")
            logger.info(f"All info axes: {all_info_reference.axes}")
    else:
        logger.warning("Answer concept reference is None")