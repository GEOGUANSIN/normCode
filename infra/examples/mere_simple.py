import os
import sys
import logging
from typing import Any, Dict, List, Optional

# Ensure this directory is importable regardless of where the script is run from
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import core components
try:
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates


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


def run_simple_sequence() -> BaseStates:

	concept_to_infer, value_concepts, function_concept = _build_demo_concepts()

	# Create inference instance configured for the simple sequence
	inference = Inference(
		"simple",
		concept_to_infer,
		function_concept,
		value_concepts,
	)

	agent = AgentFrame("demo")

	agent.configure(inference, "simple")

	inference.execute()



if __name__ == "__main__":
	run_simple_sequence() 