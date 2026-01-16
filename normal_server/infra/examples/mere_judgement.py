import os
import sys
import logging
from typing import Any, Dict, List, Optional, Callable
from types import SimpleNamespace

# Ensure the project root is in the Python path so we can import from infra
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)  # Go up one level to project root
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import core components
try:
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body


# --- Demo Setup ---

def _build_demo_concepts() -> tuple[Concept, List[Concept], Concept]:
    logger = logging.getLogger(__name__)
    logger.info("Building demo concepts")

    ref_a = Reference(axes=["a"], shape=(1,))
    ref_a.set(8, a=0)
    logger.info(f"ref_a: {ref_a.tensor}")
    concept_a = Concept(name="A", context="a", reference=ref_a, type="{}")

    ref_b = Reference(axes=["b"], shape=(1,))
    ref_b.set(4, b=0)
    logger.info(f"ref_b: {ref_b.tensor}")
    concept_b = Concept(name="B", context="b", reference=ref_b, type="{}")

    # Function concept is now a judgement normcode string
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set("::<{1}<$({number})%_> is_greater_than {2}<$({number})%_>>", f=0)
    function_concept = Concept(name="::<{1}<$({number})%_> is_greater_than {2}<$({number})%_>>", context="judging if number 1 is greater than number 2", type="::", reference=ref_f)
    logger.info(f"ref_f: {ref_f.tensor}")

    concept_to_infer = Concept(name="judgement", context="judgement result", type="{}")
    return concept_to_infer, [concept_a, concept_b], function_concept


def _build_demo_working_interpretation() -> Dict[str, Any]:
	return {
		"is_greater_than": {
			"value_order": {"A": 0, "B": 1}
		},
		"condition": "True"
	}


# --- Main Execution ---

def run_judgement_sequence() -> BaseStates:

	concept_to_infer, value_concepts, function_concept = _build_demo_concepts()

	inference = Inference(
		"judgement",
		concept_to_infer,
		function_concept,
		value_concepts,
	)

	agent = AgentFrame("demo", working_interpretation=_build_demo_working_interpretation(), body=Body())

	agent.configure(inference, "judgement")

	states = inference.execute()
	

	final_ref = states.get_reference("inference", "OR")
	if isinstance(final_ref, Reference):
		logging.getLogger(__name__).info("Final Judgement Output (OR):")
		logging.getLogger(__name__).info(f"\tAxes: {final_ref.axes}")
		logging.getLogger(__name__).info(f"\tShape: {final_ref.shape}")
		logging.getLogger(__name__).info(f"\tTensor: {final_ref.tensor}")
		# Also print to be sure we see it
		print("--- Final Judgement Output (OR) ---")
		print(f"Axes: {final_ref.axes}")
		print(f"Shape: {final_ref.shape}")
		print(f"Tensor: {final_ref.tensor}")
	
	return states


if __name__ == "__main__":
	run_judgement_sequence() 