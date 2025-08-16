import os
import sys
import logging
from typing import Any, Dict, List, Optional

# Ensure this directory is importable regardless of where the script is run from
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from _inference import Inference, register_inference_sequence, setup_logging
from _concept import Concept
from dataclasses import dataclass, field
from _reference import Reference, cross_product


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


class States:
	"""State container inspired by _syntax model_state but self-contained."""
	def __init__(self) -> None:
		self.sequence_state = SequenceSpecLite(
			sequence=[
				SequenceStepSpecLite(step_name="IWI", step_index=1),
				SequenceStepSpecLite(step_name="IR", step_index=2),
				SequenceStepSpecLite(step_name="OR", step_index=3),
				SequenceStepSpecLite(step_name="OWI", step_index=4),
			],
			current_step="IWI",
		)
		self.function: List[ReferenceRecordLite] = []
		self.values: List[ReferenceRecordLite] = []
		self.context: List[ReferenceRecordLite] = []
		self.inference: List[ReferenceRecordLite] = [
			ReferenceRecordLite(step_name="OR", reference=None)
		]


	def set_current_step(self, name: str) -> None:
		self.sequence_state.current_step = name

	def get_or_reference(self) -> Reference | None:
		for i in self.inference:
			if i.step_name == "OR":
				return i.reference
		return None

	def set_or_reference(self, ref: Reference | None) -> None:
		for i in self.inference:
			if i.step_name == "OR":
				i.reference = ref
				break


def input_working_interpretation(inference: Inference, states: States, body: Dict[str, Any] | None = None, working_interpretation: Dict[str, Any] | None = None) -> States:
	"""Initialize states with sequence info; other lists are empty initially."""
	# Sequence (fallback to default if not provided)
	wi = working_interpretation or {}
	seq = wi.get("sequence")
	if isinstance(seq, list) and all(isinstance(x, dict) and "step_name" in x for x in seq):
		states.sequence_state.sequence = [
			SequenceStepSpecLite(step_name=x.get("step_name"), step_index=x.get("step_index")) for x in seq
		]
	
	# Initialize other lists as empty, they will be populated by IR/other steps
	states.function = []
	states.values = []
	states.context = []
	
	inf_entries = wi.get("inference") or []
	# ensure OR slot exists even if not provided
	has_or = any((e.get("step_name") == "OR") for e in inf_entries)
	if not has_or:
		inf_entries.append({"step_name": "OR"})
	states.inference = [ReferenceRecordLite(step_name=ie.get("step_name")) for ie in inf_entries]

	states.set_current_step("IWI")
	return states

def input_references(inference: Inference, states: States) -> States:
	"""Populate references and concept info into the state from the inference instance."""
	
	# Function concept (should only be one in this simple demo)
	func = inference.function_concept
	if isinstance(func, Concept):
		states.function = [
			ReferenceRecordLite(
				step_name="IR", # Or from WI if available
				concept=ConceptInfoLite(
					id=func.id,
					name=func.name,
					type=func.type,
					context=func.context,
					axis_name=func.axis_name,
				),
				reference=func.reference if isinstance(func.reference, Reference) else None,
			)
		]

	# Value concepts
	states.values = []
	for vc in inference.value_concepts or []:
		if isinstance(vc, Concept):
			states.values.append(
				ReferenceRecordLite(
					step_name="IR", # Or from WI if available
					concept=ConceptInfoLite(
						id=vc.id,
						name=vc.name,
						type=vc.type,
						context=vc.context,
						axis_name=vc.axis_name,
					),
					reference=vc.reference if isinstance(vc.reference, Reference) else None,
				)
			)
	
	# Context concepts (if any)
	states.context = []
	for ctx_concept in inference.context_concepts or []:
		if isinstance(ctx_concept, Concept):
			states.context.append(
				ReferenceRecordLite(
					step_name="IR", # Or from WI if available
					concept=ConceptInfoLite(
						id=ctx_concept.id,
						name=ctx_concept.name,
						type=ctx_concept.type,
						context=ctx_concept.context,
						axis_name=ctx_concept.axis_name,
					),
					reference=ctx_concept.reference if isinstance(ctx_concept.reference, Reference) else None,
				)
			)

	states.set_current_step("IR")
	return states


def output_reference(states: States) -> States:
	"""Set OR reference. For demo: cross product of function and value references if present, else first available."""
	refs: List[Reference] = []
	if states.function and isinstance(states.function[0].reference, Reference):
		refs.append(states.function[0].reference)
	for v in states.values:
		ref = v.reference
		if isinstance(ref, Reference):
			refs.append(ref)

	final_ref: Optional[Reference] = None
	if len(refs) == 1:
		final_ref = refs[0]
	elif len(refs) > 1:
		final_ref = cross_product(refs)

	states.set_or_reference(final_ref)
	states.set_current_step("OR")
	return states


def output_working_interpretation(states: States) -> States:
	"""No-op finalization for simple demo."""
	states.set_current_step("OWI")
	return states


@register_inference_sequence("simple")
def simple(self: Inference, input_data: Dict[str, Any] | None = None) -> States:
	"""Simple sequence: IWI -> IR -> OR -> OWI using the minimal States container."""
	states = States()
	states = self.IWI(inference=self, states=states, body={}, working_interpretation=(input_data or {}).get("working_interpretation"))
	states = self.IR(inference=self, states=states)
	states = self.OR(states=states)
	states = self.OWI(states=states)
	return states


def _build_demo_concepts() -> tuple[Concept, List[Concept], Concept]:
	# Value concepts A, B
	ref_a = Reference(axes=["a"], shape=(1,), initial_value=None)
	ref_a.set(2, a=0)
	concept_a = Concept(name="A", context="a", reference=ref_a, type="{}")

	ref_b = Reference(axes=["b"], shape=(1,), initial_value=None)
	ref_b.set(3, b=0)
	concept_b = Concept(name="B", context="b", reference=ref_b, type="{}")

	value_concepts = [concept_a, concept_b]

	# Function concept: a label for this demo
	ref_func = Reference(axes=["f"], shape=(1,), initial_value=None)
	ref_func.set("SUM", f=0)
	function_concept = Concept(name="sum", context="sum", reference=ref_func, type="::")

	# Concept to infer (result) used for metadata only in this demo
	result_ref = Reference(axes=["result"], shape=(1,), initial_value=None)
	concept_to_infer = Concept(name="result", context="result", reference=result_ref, type="{}")

	return concept_to_infer, value_concepts, function_concept


def run_simple_sequence() -> States:
	setup_logging(logging.DEBUG)

	concept_to_infer, value_concepts, function_concept = _build_demo_concepts()

	# Create inference instance configured for the simple sequence
	inference = Inference(
		"simple",
		concept_to_infer,
		value_concepts,
		function_concept,
	)

	# Bind steps to this instance
	@inference.register_step("IWI")
	def IWI(**fkwargs):
		return input_working_interpretation(**fkwargs)

	@inference.register_step("IR")
	def IR(**fkwargs):
		return input_references(**fkwargs)

	@inference.register_step("OR")
	def OR(**fkwargs):
		return output_reference(**fkwargs)

	@inference.register_step("OWI")
	def OWI(**fkwargs):
		return output_working_interpretation(**fkwargs)

	# Execute and log final output
	states = simple(inference, {})
	ref = states.get_or_reference()
	if isinstance(ref, Reference):
		logging.getLogger(__name__).info("Final Output (OR):")
		logging.getLogger(__name__).info(f"\tAxes: {ref.axes}")
		logging.getLogger(__name__).info(f"\tShape: {ref.shape}")
		logging.getLogger(__name__).info(f"\tTensor: {ref.tensor}")
	return states


if __name__ == "__main__":
	run_simple_sequence() 