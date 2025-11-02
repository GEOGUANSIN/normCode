
'''
Demo script for the integrated assigning sequence in the NormCode framework.

This script demonstrates how to use the assigning sequence that has been integrated into the main infra framework.
It shows both specification ($.) and continuation ($+) operations.

The purpose of the assigning sequence is to handle syntatical concepts like this:
- Specification: $.(_a_:_b_), which takes concept _a_'s reference and assigns it to concept _b_'s reference
- Continuation: $+(_a_:_b_), which takes concept _a_'s reference and adds it to concept _b_'s reference
'''

import os
import sys
import logging
from typing import Any, List

# Configure logging to show INFO messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the project root is in the Python path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import core components
try:
    from infra import Inference, Concept, Reference, AgentFrame, Body
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
    from infra import Inference, Concept, Reference, AgentFrame, Body


def _as_list(data: Any) -> List:
    """Ensures the provided data is a list."""
    return data if isinstance(data, list) else [data]


def run_assigning_demo(demo_title: str, marker: str, concept_a_val: Any, concept_b_val: Any, concept_c_val: Any, assign_source: Any = None):
    """Sets up and runs a single assigning demonstration using the integrated infra framework."""
    logger.info(f"\n----- {demo_title} -----")

    # 1. Setup concepts and working interpretation
    concept_a = Concept("a")
    concept_a.reference = Reference.from_data(_as_list(concept_a_val))

    concept_b = Concept("b")
    concept_b.reference = Reference.from_data(_as_list(concept_b_val))

    concept_c = Concept("c")
    concept_c.reference = Reference.from_data(_as_list(concept_c_val))

    final_assign_source = assign_source if assign_source is not None else concept_a.name

    working_interpretation = {
        "syntax": {
            "marker": marker,
            "assign_source": final_assign_source,
            "assign_destination": concept_b.name
        }
    }

    logger.info(f"Initial state: Concept 'a' ref: {concept_a.reference.get()}, Concept 'b' ref: {concept_b.reference.get()}, Concept 'c' ref: {concept_c.reference.get()}")
    logger.info(f"Working interpretation: {working_interpretation}")

    # 2. Setup agent and inference
    body = Body()
    agent_frame = AgentFrame("demo", working_interpretation, body=body)
    
    assigning_concept = Concept("assigning")
    concept_target = concept_b.copy()

    inference = Inference(
        sequence_name="assigning",
        concept_to_infer=concept_target,
        function_concept=assigning_concept,
        value_concepts=[concept_a, concept_b, concept_c],
    )

    # 3. Configure and run the sequence
    agent_frame.configure(inference, "assigning")
    result_states = inference.execute()

    # 4. Log the result
    final_reference = result_states.get_reference("inference", "OR")
    if final_reference:
        logger.info(f"Final output reference: {final_reference.get()}")
    else:
        logger.warning("Sequence did not produce an output reference.")
    logger.info("----- Demo Complete -----")


if __name__ == "__main__":
    # Demo 1: Specification ($.) - Assigns a's reference to b
    run_assigning_demo(
        demo_title="Demo 1: Specification ($.)",
        marker=".",
        concept_a_val=[{"id": 1, "data": "This is from A"}],
        concept_b_val=["Original value of B"],
        concept_c_val="I am irrelevant context",
        assign_source="a"
    )

    # Demo 2: Continuation ($+) - Appends a's list to b's list
    run_assigning_demo(
        demo_title="Demo 2: Continuation ($+)",
        marker="+",
        concept_a_val=[1, 2, 3],
        concept_b_val=["x", "y", "z"],
        concept_c_val=["more", "irrelevant", "context"],
        assign_source="a"
    )

    # Demo 3: Prioritized Specification - First source ('a') is empty, uses 'c'
    run_assigning_demo(
        demo_title="Demo 3: Prioritized Specification - First source ('a') is empty, uses 'c'",
        marker=".",
        concept_a_val=[],  # Empty reference
        concept_b_val=["Original value of B"],
        concept_c_val=["This is from C"],
        assign_source=['a', 'c']
    )

    # Demo 4: Prioritized Specification - First source ('a') is valid, so 'c' is ignored
    run_assigning_demo(
        demo_title="Demo 4: Prioritized Specification - First source ('a') is valid",
        marker=".",
        concept_a_val=["This is from A"],
        concept_b_val=["Original value of B"],
        concept_c_val=["This is from C, but will not be used"],
        assign_source=['a', 'c']
    )

    # Demo 5: Prioritized Specification - All sources empty, falls back to destination 'b'
    run_assigning_demo(
        demo_title="Demo 5: Prioritized Specification - All sources empty, falls back to 'b'",
        marker=".",
        concept_a_val=[],  # Empty
        concept_b_val=["Original value of B"],  # Destination
        concept_c_val=[],  # Empty
        assign_source=['a', 'c']
    )






