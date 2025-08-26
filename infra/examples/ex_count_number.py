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


# --- Demo Setup: Counting Digits from a Number ---

def _build_demo_concepts_for_number_count(number: str) -> tuple[Concept, List[Concept], Concept, List[Concept]]:
    """Builds concepts for the outer quantification controller."""
    # The number to be deconstructed, provided as a value concept.
    # The quantification loop will iterate based on this value's state.
    ref_number = Reference(axes=["val"], shape=(1,))
    ref_number.set(f"%({number})", val=0)
    concept_number = Concept("{number}", "number", "val", ref_number)

    # Context Concepts for Loop Control - both number and index are needed.
    concept_current_number = Concept("{number}*", "number*", "number*")
    concept_loop_index = Concept("{index}*", "index*", "index*")

    # Placeholder for the function concept, which will be the *result* of the inner imperative step.
    # It will hold the extracted {index, digit} pair.
    # Following user's edit to use '*every()' as the name.
    quantification_concept = Concept("*every()", "extraction_result", "f", Reference(axes=["f"], shape=(1,)))

    # Concept to Infer: The final list of extracted digits and their indices.
    concept_to_infer = Concept("{counted_digits}", "counted_digits", "counted_digits")

    return (
        concept_to_infer,
        [concept_number],
        quantification_concept,
        [concept_current_number, concept_loop_index]
    )

def _build_demo_working_interpretation() -> Dict[str, Any]:
    """Provides the syntax needed for the QR step."""
    return {
        "syntax": {
            "marker": None,
            # The LoopBaseConcept is the concept that the quantifier iterates over.
            # Its value is static and only used to determine the number of iterations.
            "LoopBaseConcept": "{number}",
            "ConceptToInfer": ["{counted_digits}"],
            # InLoopConcepts are carried over between iterations.
            "InLoopConcept": {
                # "{number}*"  loop base concept is not an inloop concept, but it is a context concept
                "{index}*": 1           # The incrementing index
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

def run_number_counting_sequence(number: str = "120738") -> BaseStates:
    """Demonstrates a dynamic quantification loop that deconstructs a number."""

    # --- Mock Inner "Imperative" Sequence ---
    def mock_imperative_remove_last_digit(current_number_concept: Concept, index_concept: Concept, number_state_concept: Concept) -> Tuple[Optional[Concept], Optional[Concept]]:
        """
        Simulates an inner worker that returns two concepts:
        1. The output concept for collection (e.g., {index, digit}).
        2. The next state concept containing the appended list of numbers.
        """
        try:
            number_str = str(current_number_concept.reference.copy().tensor[0]).strip("%()")
        except (AttributeError, IndexError, ValueError, TypeError):
            number_str = ""
        
        try:
            current_index = int(str(index_concept.reference.copy().tensor[0]).strip("%()"))
        except (AttributeError, IndexError, ValueError, TypeError):
            current_index = 0 # Starts at 0

        if not number_str or not number_str.isdigit():
            logging.warning(f"[Inner Worker] Number is empty or invalid ('{number_str}'). Signaling termination.")
            return None, None

        # Core Logic
        last_digit = number_str[-1]
        new_number_str = number_str[:-1]
        new_index = current_index + 1

        # 1. Create the output concept for collection
        result_str = f"index: {new_index}, digit: {last_digit}"
        logging.info(f"[Inner Worker] Extracted: '{result_str}'.")
        ref_output = Reference(axes=["val"], shape=(1,)); ref_output.set(f"%({result_str})", val=0)
        output_concept = Concept("*every()", "extraction_result", "val", ref_output)

        # 2. Create the concept for the next loop's state by appending to the tensor
        logging.info(f"[Inner Worker] New number state for next loop: '{new_number_str or 'empty'}'")
        
        # Get the existing tensor and append the new number string, if it's not already present.
        existing_tensor = list(number_state_concept.reference.tensor)
        if new_number_str:
            new_val_to_add = f"%({new_number_str})"
            if new_val_to_add not in existing_tensor:
                existing_tensor.append(new_val_to_add)

        # Create a new Reference and Concept from the updated tensor
        new_shape = (len(existing_tensor),)
        new_axes = number_state_concept.reference.axes
        axis_name = new_axes[0] if new_axes else "val" # Fallback axis name
        new_ref = Reference(axes=new_axes, shape=new_shape)
        for i, v in enumerate(existing_tensor):
            new_ref.set(v, **{axis_name: i})
        
        next_number_concept = Concept("{number}", "number", "val", new_ref)

        # 3. Create a new index concept
        ref_index = Reference(axes=["val"], shape=(1,)); ref_index.set(f"%({new_index})", val=0)
        index_concept = Concept("{index}", "index", "val", ref_index)

        return output_concept, next_number_concept, index_concept

    # --- Setup for Outer "Quantifying" Controller ---
    concept_to_infer, value_concepts, quantification_concept, context_concepts = _build_demo_concepts_for_number_count(number)
    initial_number_concept = value_concepts[0]

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
    
    # The initial state is created by running the sequence once.
    agent = AgentFrame("demo", working_interpretation=working_interpretation, body=Body())
    agent.configure(quantification_inference, "quantifying")
    states = quantification_inference.execute()
    
    number_state_concept = initial_number_concept
    current_index_val = 0 # Manual tracking for the index

    while not working_interpretation.get("syntax", {}).get("completion_status", False):
        iteration += 1
        logging.info(f"--- QUANTIFICATION LOOP: ITERATION {iteration} ---")
        if iteration > 100: # Safety break
            logging.warning("Safety break triggered to prevent infinite loop.")
            break

        # 1. Run the controller to get the current state for the inner worker
        logging.info("[Controller] Running to get context for inner worker...")
        
        working_interpretation["workspace"] = states.workspace.copy()

        quantification_inference.value_concepts = [number_state_concept]
        
        
        agent = AgentFrame("demo", working_interpretation=working_interpretation, body=Body())
        agent.configure(quantification_inference, "quantifying")
        states = quantification_inference.execute()
        
        workspace_tensor_view = _get_workspace_tensor_view(states.workspace)
        logging.info(f"[Controller] Workspace after execution: {workspace_tensor_view}")

        # Check if the loop is complete right after the execution runs
        if states.syntax.completion_status == True:
            logging.info("[Controller] Loop is complete based on internal state. Exiting loop.")
            break

        # Extract the state from the context provided by the controller
        current_number_ctx = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{number}*"), initial_number_concept)
        index_ctx = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{index}*"), Concept("","", "", Reference(axes=[], shape=())))
        
        # 2. Run the inner worker (mocked) with the context provided by the controller
        logging.info(f"[Controller] Current number context for worker: {current_number_ctx.reference.tensor}")
        logging.info(f"[Controller] Index context for worker: {index_ctx.reference.tensor}")
        logging.info(f"[Controller] Number state concept for worker: {number_state_concept.reference.tensor}")
        output_concept, next_number_concept, index_concept = mock_imperative_remove_last_digit(current_number_ctx, index_ctx, number_state_concept)

        # If worker returns None, it means the loop is done.
        if output_concept is None or next_number_concept is None:
            working_interpretation["syntax"]["completion_status"] = True
            logging.info("[Controller] Worker signaled completion. Exiting loop.")
            break
            
        # 3. Feed the results back to the controller for the *next* iteration
        quantification_inference.function_concept = output_concept
        quantification_inference.value_concepts = [next_number_concept]
        number_state_concept = next_number_concept
        
        # 4. Renew the context concepts in the states object
        [concept_current_number, concept_loop_index] = context_concepts
        concept_current_number.reference = current_number_ctx.reference.copy()
        concept_loop_index.reference = index_concept.reference.copy()
        quantification_inference.context_concepts = [concept_current_number, concept_loop_index]

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
        print(f"Tensor: {tensor_content}")
        # Expected: [['%(index: 1, digit: 8)'], ['%(index: 2, digit: 3)'], ..., ['%(index: 6, digit: 1)']]
    
    return final_states

if __name__ == "__main__":
    run_number_counting_sequence('67894567894567895678') 