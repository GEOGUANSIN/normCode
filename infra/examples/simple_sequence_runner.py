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
from _states.simple_states import States
from ._steps.simple import iwi, ir, or_step, owi


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
		return iwi.input_working_interpretation(**fkwargs)

	@inference.register_step("IR")
	def IR(**fkwargs):
		return ir.input_references(**fkwargs)

	@inference.register_step("OR")
	def OR(**fkwargs):
		return or_step.output_reference(**fkwargs)

	@inference.register_step("OWI")
	def OWI(**fkwargs):
		return owi.output_working_interpretation(**fkwargs)

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