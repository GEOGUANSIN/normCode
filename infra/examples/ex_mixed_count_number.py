import os
import sys
import logging
from typing import Any, Dict, List, Optional, Tuple
import json
import random
import re

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
    from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
    from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body


# --- Utilities for Parsing Imperative Worker Output ---

def parse_imperative_output(output_tensor: Any) -> Optional[str]:
    """
    Parses the output tensor from an imperative inference to extract a single string value.
    Handles various formats like nested lists, JSON, and wrapped strings.
    """
    if output_tensor is None:
        return None
    try:
        result_str = str(output_tensor)

        # Navigate through nested list/tuple if necessary
        if isinstance(output_tensor, (list, tuple)):
            def find_string_in_nested(obj):
                if isinstance(obj, str): return obj
                if isinstance(obj, (list, tuple)) and len(obj) > 0:
                    return find_string_in_nested(obj[0])
                return str(obj)
            result_str = find_string_in_nested(output_tensor)

        # Remove %(...) wrapper
        if result_str.startswith("%(") and result_str.endswith(")"):
            result_str = result_str[2:-1]

        # Try to parse as JSON
        try:
            data = json.loads(result_str)
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                if isinstance(item, dict):
                    # Look for common keys
                    for key in ['last_digit', 'digit', 'number', 'result']:
                        if key in item:
                            return str(item[key])
                return str(item)
            else:
                 return str(data)
        except json.JSONDecodeError:
            # Not JSON, so treat as a simple string
            pass

        # Handle list-like string representation like "['123']"
        if result_str.startswith('[') and result_str.endswith(']'):
            result_str = result_str[1:-1].strip()

        # Remove quotes if present, e.g., "'123'"
        if (result_str.startswith("'") and result_str.endswith("'")) or \
           (result_str.startswith('"') and result_str.endswith('"')):
            result_str = result_str[1:-1]

        return result_str.strip()

    except Exception as e:
        logger.error(f"Error parsing output tensor: {e}")
        return None


# --- Concept Builders for Inner "Imperative" Workers ---

def _build_get_digit_concepts(number_to_analyze: str, normcode_string: str) -> tuple[Concept, List[Concept], Concept]:
    """Builds concepts for the 'get last digit' imperative inference."""
    # Input concept
    ref_num = Reference(axes=["num1"], shape=(1,))
    ref_num.set(number_to_analyze, num1=0)
    concept_num = Concept(name="number", context="The number to find the last digit of", reference=ref_num, type="{}")

    # Concept describing what to get
    ref_last_digit = Reference(axes=["last_digit"], shape=(1,))
    ref_last_digit.set("1 digit counting from the right", last_digit=0)
    concept_last_digit = Concept(name="unit place value", context="The rightmost digit", reference=ref_last_digit, type="{}")

    # Function concept
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set(normcode_string, f=0)
    function_concept = Concept(name=normcode_string, context="Get the last digit of a number", type="::", reference=ref_f)

    # Concept to be inferred
    concept_to_infer = Concept(name="unit place digit", context="The resulting unit place digit", type="{}")

    return concept_to_infer, [concept_num, concept_last_digit], function_concept


def _build_remove_digit_concepts(number_to_analyze: str, normcode_string: str) -> tuple[Concept, List[Concept], Concept]:
    """Builds concepts for the 'remove last digit' imperative inference."""
    # Input concept
    ref_num = Reference(axes=["number"], shape=(1,))
    ref_num.set(number_to_analyze, number=0)
    concept_num = Concept(name="number", context="The number to remove the digit from", reference=ref_num, type="{}")

    # Concept describing what to remove
    ref_unit_place = Reference(axes=["unit_place"], shape=(1,))
    ref_unit_place.set("the rightmost digit", unit_place=0)
    concept_unit_place = Concept(name="unit place digit", context="The rightmost digit to remove", reference=ref_unit_place, type="{}")

    # Function concept
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set(normcode_string, f=0)
    function_concept = Concept(name=normcode_string, context="Remove the last digit", type="::", reference=ref_f)

    # Concept to be inferred
    concept_to_infer = Concept(name="number without unit place", context="The number with the last digit removed", type="{}")

    return concept_to_infer, [concept_num, concept_unit_place], function_concept


def _build_imperative_wi(normcode_string: str, concept1_name: str, concept2_name: str) -> Dict[str, Any]:
    """Builds a generic working interpretation for the imperative steps."""
    return {
        "is_relation_output": False,
        "with_thinking": True,
        normcode_string: {
            "value_order": {
                concept1_name: 0,
                concept2_name: 1
            }
        }
    }


# --- Live Imperative Worker ---

def live_imperative_worker(current_number_str: str, current_index: int, number_state_concept: Concept) -> Tuple[Optional[Concept], Optional[Concept], Optional[Concept]]:
    """
    Replaces the mock worker. Runs two live imperative inferences to:
    1. Get the last digit of the current number.
    2. Remove the last digit to produce the number for the next state.
    """
    logger.info(f"[Live Worker] Iteration {current_index + 1} | Processing number: '{current_number_str}'")

    if not current_number_str or not current_number_str.isdigit():
        logger.warning("[Live Worker] Number is empty or invalid. Signaling termination.")
        return None, None, None

    # --- 1. Inference to GET the last digit ---
    get_digit_normcode = "::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)"
    concept_to_infer_get, val_concepts_get, func_concept_get = _build_get_digit_concepts(current_number_str, get_digit_normcode)

    inference_get = Inference("imperative", concept_to_infer_get, val_concepts_get, func_concept_get)
    agent_get = AgentFrame("demo", working_interpretation=_build_imperative_wi(get_digit_normcode, "number", "unit place value"), body=Body())
    agent_get.configure(inference_get, "imperative")
    states_get = inference_get.execute()

    final_ref_get = states_get.get_reference("inference", "OR")
    last_digit = parse_imperative_output(final_ref_get.tensor if final_ref_get else "")

    if last_digit is None:
        logger.error("[Live Worker] Failed to extract last digit. Terminating.")
        return None, None, None

    # --- 2. Inference to REMOVE the last digit ---
    remove_digit_normcode = "::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)"
    concept_to_infer_rem, val_concepts_rem, func_concept_rem = _build_remove_digit_concepts(current_number_str, remove_digit_normcode)

    inference_rem = Inference("imperative", concept_to_infer_rem, val_concepts_rem, func_concept_rem)
    agent_rem = AgentFrame("demo", working_interpretation=_build_imperative_wi(remove_digit_normcode, "number", "unit place digit"), body=Body())
    agent_rem.configure(inference_rem, "imperative")
    states_rem = inference_rem.execute()

    final_ref_rem = states_rem.get_reference("inference", "OR")
    new_number_str = parse_imperative_output(final_ref_rem.tensor if final_ref_rem else "")

    # An empty string for the new number is a valid outcome for the last digit
    if new_number_str is None:
        new_number_str = ""
        logger.info("[Live Worker] Number is now empty after removing the last digit.")

    new_index = current_index + 1

    # --- 3. Construct output concepts for the quantifier controller ---
    # a. Output concept for collection (the {index, digit} pair)
    result_str = f"index: {new_index}, digit: {last_digit}"
    logger.info(f"[Live Worker] Extracted: '{result_str}'.")
    ref_output = Reference(axes=["val"], shape=(1,)); ref_output.set(f"%({result_str})", val=0)
    output_concept = Concept("*every()", "extraction_result", "val", ref_output)

    # b. Next state concept containing the new, shorter number
    logger.info(f"[Live Worker] New number for next loop: '{new_number_str or 'empty'}'")
    existing_tensor = list(number_state_concept.reference.tensor)
    if new_number_str:
        new_val_to_add = f"%({new_number_str})"
        if new_val_to_add not in existing_tensor:
            existing_tensor.append(new_val_to_add)

    new_shape = (len(existing_tensor),)
    new_axes = number_state_concept.reference.axes
    axis_name = new_axes[0] if new_axes else "val"
    new_ref = Reference(axes=new_axes, shape=new_shape)
    for i, v in enumerate(existing_tensor):
        new_ref.set(v, **{axis_name: i})
    next_number_concept = Concept("{number}", "number", "val", new_ref)

    # c. New index concept
    ref_index = Reference(axes=["val"], shape=(1,)); ref_index.set(f"%({new_index})", val=0)
    index_concept = Concept("{index}", "index", "val", ref_index)

    return output_concept, next_number_concept, index_concept


# --- Demo Setup: Quantifying Controller ---

def _build_quantifier_concepts(number: str) -> tuple[Concept, List[Concept], Concept, List[Concept]]:
    """Builds concepts for the outer quantification controller."""
    ref_number = Reference(axes=["val"], shape=(1,))
    ref_number.set(f"%({number})", val=0)
    concept_number = Concept("{number}", "number", "val", ref_number)

    concept_current_number = Concept("{number}*", "number*", "number*")
    concept_loop_index = Concept("{index}*", "index*", "index*")

    quantification_concept = Concept("*every()", "extraction_result", "f", Reference(axes=["f"], shape=(1,)))
    concept_to_infer = Concept("{counted_digits}", "counted_digits", "counted_digits")

    return (concept_to_infer, [concept_number], quantification_concept, [concept_current_number, concept_loop_index])


def _build_quantifier_wi() -> Dict[str, Any]:
    """Provides the syntax needed for the QR (quantifier) step."""
    return {
        "syntax": {
            "marker": None,
            "LoopBaseConcept": "{number}",
            "ConceptToInfer": ["{counted_digits}"],
            "InLoopConcept": {"{index}*": 1},
            "completion_status": False
        }
    }


def _get_workspace_tensor_view(workspace: Dict) -> Dict:
    """Recursively converts a workspace of Reference objects to a dictionary of their tensors."""
    tensor_view = {}
    for key, value in workspace.items():
        if isinstance(value, dict):
            tensor_view[key] = _get_workspace_tensor_view(value)
        elif hasattr(value, 'tensor'):
            tensor_view[key] = value.tensor
        else:
            tensor_view[key] = value
    return tensor_view


def validate_digit_counting_output(input_number: str, output_tensor: Any) -> bool:
    """
    Validates that the output from the quantification sequence correctly deconstructed the number.
    Accepts overflowing zeros that do not change the integer value of the number.
    """
    logger.info("\n--- Validation ---")
    try:
        # Check for expected tensor structure: a list containing one list of strings
        if not (isinstance(output_tensor, list) and len(output_tensor) > 0 and isinstance(output_tensor[0], list)):
            logger.error(f"❌ Validation Failed: Output tensor has unexpected format: {output_tensor}")
            return False

        # The quantifier returns a list containing one list of results.
        extracted_strings = [item.strip('%()') for item in output_tensor[0] if item]
        logger.info(f"📊 Extracted {len(extracted_strings)} items from tensor.")

        # 1. Check if we have at least enough digits
        if len(extracted_strings) < len(input_number):
            logger.error(f"❌ Validation Failed: Not enough digits. Expected at least {len(input_number)}, but got {len(extracted_strings)}.")
            return False

        # 2. Parse each string to get index and digit
        digit_map = {}
        for s in extracted_strings:
            match = re.search(r"index:\s*(\d+),\s*digit:\s*(\d)", s)
            if not match:
                logger.error(f"❌ Validation Failed: Could not parse item string: '{s}'")
                return False
            index = int(match.group(1))
            digit = match.group(2)
            digit_map[index] = digit
        
        logger.info(f"📊 Parsed digit map: {digit_map}")

        # 3. Reconstruct the number from the parsed digits
        if not digit_map:
            reconstructed_reversed_number = ""
        else:
            sorted_digits = [digit_map[i] for i in sorted(digit_map.keys())]
            reconstructed_reversed_number = "".join(sorted_digits)

        logger.info(f"📊 Reconstructed reversed number: '{reconstructed_reversed_number}'")
        
        # 4. Reverse the reconstructed number string to get the number in correct order
        reconstructed_number_str = reconstructed_reversed_number[::-1]
        logger.info(f"📊 Reconstructed number string: '{reconstructed_number_str}'")

        # 5. Compare the integer values to handle leading/overflowing zeros
        try:
            reconstructed_int = int(reconstructed_number_str)
            expected_int = int(input_number)

            logger.info(f"📊 Reconstructed as integer: {reconstructed_int}")
            logger.info(f"📊 Expected as integer:    {expected_int}")

            if reconstructed_int == expected_int:
                logger.info("✅ Validation Passed! The number was deconstructed correctly.")
                return True
            else:
                logger.error("❌ Validation Failed: Reconstructed number does not match the original integer value.")
                return False
        except ValueError:
            logger.error(f"❌ Validation Failed: Could not convert reconstructed number '{reconstructed_number_str}' or input '{input_number}' to an integer for comparison.")
            return False

    except Exception as e:
        logger.error(f"❌ An unexpected error occurred during validation: {e}")
        return False


# --- Main Execution ---

def run_mixed_counting_sequence(number: str = "987", length: int = 3) -> Tuple[BaseStates, bool]:
    """
    Demonstrates a quantifying loop controller that uses live imperative agent
    calls as its inner worker to deconstruct a number.
    """
    # --- Setup for Outer "Quantifying" Controller ---
    concept_to_infer, value_concepts, quantification_concept, context_concepts = _build_quantifier_concepts(number)
    initial_number_concept = value_concepts[0]

    quantification_inference = Inference(
        "quantifying",
        concept_to_infer,
        value_concepts,
        quantification_concept,
        context_concepts=context_concepts
    )

    # --- Main Execution Loop ---
    working_interpretation = _build_quantifier_wi()
    iteration = 0

    # The initial state is created by running the sequence once.
    agent = AgentFrame("demo", working_interpretation=working_interpretation, body=Body())
    agent.configure(quantification_inference, "quantifying")
    states = quantification_inference.execute()

    number_state_concept = initial_number_concept

    while not working_interpretation.get("syntax", {}).get("completion_status", False):
        iteration += 1
        logger.info(f"--- QUANTIFICATION LOOP: ITERATION {iteration} ---")
        if iteration > length + 20:  # Safety break
            logger.warning(f"Safety break triggered after {length + 20} iterations.")
            break

        # 1. Run the controller to get the current state for the inner worker
        logger.info("[Controller] Getting context for live worker...")

        working_interpretation["workspace"] = states.workspace.copy()
        quantification_inference.value_concepts = [number_state_concept]

        agent = AgentFrame("demo", working_interpretation=working_interpretation, body=Body())
        agent.configure(quantification_inference, "quantifying")
        states = quantification_inference.execute()

        workspace_tensor_view = _get_workspace_tensor_view(states.workspace)
        logger.info(f"[Controller] Workspace state: {workspace_tensor_view}")

        if states.syntax.completion_status:
            logger.info("[Controller] Loop complete based on internal state. Exiting.")
            break

        # 2. Extract context from controller to pass to the live worker
        current_num_record = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{number}*"), None)
        try:
            # Get the reference from the record, or fall back to the initial concept's reference
            active_reference = current_num_record.reference if current_num_record else initial_number_concept.reference
            current_number_str = str(active_reference.copy().tensor[0]).strip("%()")
        except (AttributeError, IndexError):
            current_number_str = ""

        index_record = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{index}*"), None)
        try:
            # The index might not exist in the first iteration, so default to 0
            if index_record and index_record.reference and index_record.reference.tensor is not None:
                current_index = int(str(index_record.reference.copy().tensor[0]).strip("%()"))
            else:
                current_index = 0
        except (AttributeError, IndexError, ValueError):
            current_index = 0


        # 3. Run the live imperative worker
        output_concept, next_number_concept, index_concept = live_imperative_worker(current_number_str, current_index, number_state_concept)

        if output_concept is None or next_number_concept is None:
            working_interpretation["syntax"]["completion_status"] = True
            logger.info("[Controller] Worker signaled completion. Finalizing loop.")
            # Run the controller one last time to finalize the state
            agent = AgentFrame("demo", working_interpretation=working_interpretation, body=Body())
            agent.configure(quantification_inference, "quantifying")
            states = quantification_inference.execute()
            break

        # 4. Feed results from the worker back to the controller for the next iteration
        quantification_inference.function_concept = output_concept
        quantification_inference.value_concepts = [next_number_concept]
        number_state_concept = next_number_concept

        # 5. Renew context concepts in the inference object
        concept_current_number, concept_loop_index = context_concepts
        concept_current_number.reference = current_num_record.reference.copy() if current_num_record else initial_number_concept.reference.copy()
        concept_loop_index.reference = index_concept.reference.copy()
        quantification_inference.context_concepts = [concept_current_number, concept_loop_index]

        if hasattr(states, 'syntax'):
            working_interpretation["syntax"]["completion_status"] = states.syntax.completion_status

    logger.info("--- QUANTIFICATION COMPLETE ---")
    final_ref = states.get_reference("inference", "OR")

    validation_result = False
    if isinstance(final_ref, Reference):
        tensor_content = final_ref.get_tensor(ignore_skip=True)
        logger.info(f"Final Tensor: {tensor_content}")
        print("\n--- Final Output (OR) ---")
        print(f"Tensor: {tensor_content}")
        # Expected for "987": [['%(index: 1, digit: 7)'], ['%(index: 2, digit: 8)'], ['%(index: 3, digit: 9)']]
        
        validation_result = validate_digit_counting_output(number, tensor_content)
        if validation_result:
            print("🎉 All tests passed!")
        else:
            print("💥 Validation failed!")


    return states, validation_result


def generate_random_number(length: int) -> str:
    """
    Generate a random number string of specified length.
    
    Args:
        length: The desired length of the number (number of digits)
        
    Returns:
        A string representing a random number with the specified length
        
    Note:
        - The first digit will never be 0 to ensure it's a valid positive number
        - Length must be at least 1
    """
    if length < 1:
        raise ValueError("Length must be at least 1")
    
    # Generate first digit (1-9 to avoid leading zeros)
    first_digit = str(random.randint(1, 9))
    
    # Generate remaining digits (0-9)
    remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(length - 1))
    
    return first_digit + remaining_digits

if __name__ == "__main__":
    # Use a short number for demonstration to keep the logs readable
    length = 150
    number = generate_random_number(length)
    _, result = run_mixed_counting_sequence(number=number, length=length)
    print(f"\nInput number was: {number}")
    print(f"Validation Result: {'✅ PASSED' if result else '❌ FAILED'}")
