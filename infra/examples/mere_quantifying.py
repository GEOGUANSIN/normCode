import os
import sys
import logging
from typing import Any, Dict, List, Optional, Callable, Tuple
from types import SimpleNamespace
from dataclasses import dataclass, field
from string import Template
from copy import copy

# Configure logging to show DEBUG messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# Ensure this directory is importable regardless of where the script is run from
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import core components
try:
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body


# --- Demo Setup: Summing Digits ---

def _build_demo_concepts_for_quant_controller() -> tuple[Concept, List[Concept], Concept, List[Concept]]:
    """Builds concepts for the outer quantification controller."""
    # Value Concept: The list of digits to be looped over.
    ref_digits = Reference(axes=["digit_pos"], shape=(4,))
    for i, v in enumerate([1, 8, 2, 5]):
        ref_digits.set(f"%({v})", digit_pos=i)
    concept_digits = Concept("{digit}", "digit", "digit_pos", ref_digits)

    # Context Concepts for Loop Control
    concept_current_digit = Concept("{digit}*", "digit*", "digit*")
    concept_partial_sum = Concept("{partial_sum}*", "partial_sum*", "partial_sum*")

    # Placeholder for the function concept, which will be the *result* of the inner imperative step
    quantification_concept = Concept("::(add_result)", "add_result", "f", Reference(axes=["f"], shape=(1,)))

    # Concept to Infer: The final accumulated sum.
    concept_to_infer = Concept("{sum}", "sum", "sum")

    return (
        concept_to_infer,
        [concept_digits],
        quantification_concept,
        [concept_current_digit, concept_partial_sum]
    )

def _build_demo_working_interpretation() -> Dict[str, Any]:
    """Provides the syntax needed for the QR step."""
    return {
        "syntax": {
            "marker": None, 
            "LoopBaseConcept": "{digit}",
            "ConceptToInfer": ["{sum}"],
            "InLoopConcept": {
                "{partial_sum}*": 1  # Carry over partial sum from 1 step ago
            },
            "completion_status": False
        }
    }

# --- Utility Functions ---
def _get_workspace_tensor_view(workspace: Dict) -> Dict:
    """Recursively converts a workspace of Reference objects to a dictionary of their tensors."""
    tensor_view = {}
    for key, value in workspace.items():
        if isinstance(value, dict):
            tensor_view[key] = _get_workspace_tensor_view(value)
        elif hasattr(value, 'tensor'): # Check if it's a Reference-like object
            tensor_view[key] = value.tensor
        else:
            tensor_view[key] = value
    return tensor_view

# --- Main Execution ---

def run_quantifying_sequence() -> BaseStates:
    """Demonstrates the iterative controller-actor pattern for quantification."""

    # --- Mock Inner "Imperative" Sequence ---
    def mock_imperative_add_step(current_digit_concept: Concept, partial_sum_concept: Concept) -> Concept:
        """Simulates an inner sequence that performs addition for one loop step."""
        # Strip wrappers like %() to get raw numbers
        try:
            current_digit = int(str(current_digit_concept.reference.copy().tensor[0]).strip("%()"))
        except (AttributeError, IndexError, ValueError):
            current_digit = 0
        try:
            partial_sum = int(str(partial_sum_concept.reference.copy().tensor[0]).strip("%()"))
        except (AttributeError, IndexError, ValueError, TypeError):
            partial_sum = 1  # Default to 0 if no partial sum yet

        new_sum = current_digit + partial_sum
        logging.info(f"[Inner Worker] Adding {current_digit} + {partial_sum} = {new_sum}")

        # The result is a new concept holding the calculated sum
        ref_new_sum = Reference(axes=["sum"], shape=(1,)); ref_new_sum.set(f"%({new_sum})", sum=0)
        return Concept("{new_sum}", "new_sum", "sum", ref_new_sum)

    # --- Setup for Outer "Quantifying" Controller ---
    concept_to_infer, value_concepts, quantification_concept, context_concepts = _build_demo_concepts_for_quant_controller()
    
    quantification_inference = Inference(
        "quantifying",
        concept_to_infer,
        quantification_concept, # Starts with a placeholder
        value_concepts,
        context_concepts=context_concepts
    )

    # --- Main Execution Loop ---
    working_interpretation = _build_demo_working_interpretation()
    iteration = 0
    
    # We need a state object that persists across loop iterations
    agent = AgentFrame("demo", working_interpretation=_build_demo_working_interpretation(), body=Body())
    agent.configure(quantification_inference, "quantifying")
    states = quantification_inference.execute()


    while not working_interpretation.get("syntax", {}).get("completion_status", False):
        iteration += 1
        logging.info(f"--- QUANTIFICATION LOOP: ITERATION {iteration} ---")
        if iteration > 5: # Safety break
            logging.warning("Safety break triggered to prevent infinite loop.")
            break

        # 1. Run the controller to get the current state and context for the inner worker
        logging.info("[Controller] Running to get context for inner worker...")
        
        # Pass the whole states object to persist workspace and other attributes
        working_interpretation["workspace"] = states.workspace.copy()
        workspace_tensor = _get_workspace_tensor_view(states.workspace); logging.info(f"Workspace tensor: {workspace_tensor}")
        
        
        agent = AgentFrame("demo", working_interpretation=working_interpretation, body=Body())
        agent.configure(quantification_inference, "quantifying")
        states = quantification_inference.execute()

        # Check if the loop is complete right after the execution runs
        if states.syntax.completion_status == True:
            logging.info("[Controller] Loop is complete. Exiting loop.")
            break

        # Extract the current digit and partial sum from the controller's 'OR' context
        current_digit_ctx = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{digit}*"), Concept("","", "", Reference(axes=[], shape=())))
        partial_sum_ctx = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{partial_sum}*"), Concept("","", "", Reference(axes=[], shape=())))

        logging.info(f"[Controller] Current digit context for worker: {current_digit_ctx.reference.tensor}")
        logging.info(f"[Controller] Partial sum context for worker: {partial_sum_ctx.reference.tensor}")

        # 2. Run the inner worker (mocked) with the context provided by the controller
        new_sum_concept = mock_imperative_add_step(current_digit_ctx, partial_sum_ctx)

        # 3. Feed the result of the inner worker back to the controller
        # The result becomes the "function_concept" for the controller's next run
        quantification_inference.function_concept = new_sum_concept

        # 4. Renew the context concepts in the states object
        [current_digit, partial_sum] = context_concepts
        current_digit.reference = current_digit_ctx.reference.copy()
        partial_sum.reference = partial_sum_ctx.reference.copy()
        quantification_inference.context_concepts = [current_digit, partial_sum]
        
        # Update the working interpretation with the latest completion status from the state
        if hasattr(states, 'syntax') and hasattr(states.syntax, 'completion_status'):
            working_interpretation["syntax"]["completion_status"] = states.syntax.completion_status
        else:
            working_interpretation["syntax"]["completion_status"] = True # Failsafe

    logging.info("--- QUANTIFICATION COMPLETE ---")
    
    # Final state after loop terminates
    final_states = states
    final_ref = final_states.get_reference("inference", "OR")

    # Final log
    logger = logging.getLogger(__name__)
    if isinstance(final_ref, Reference):
        logger.info("--- Final Output (OR) ---")
        tensor_content = final_ref.get_tensor(ignore_skip=True)
        logger.info(f"Final Tensor: {tensor_content}")
        print("\n--- Final Output (OR) ---")
        # The result is a list of all the intermediate sums
        print(f"Tensor: {tensor_content}")
        # Expected: [['%(1)'], ['%(9)'], ['%(11)'], ['%(16)']]
    
    return final_states

if __name__ == "__main__":
    run_quantifying_sequence() 