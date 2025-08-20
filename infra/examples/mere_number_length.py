import os
import sys
import logging
from typing import Any, Dict, List
import json

# Ensure the project root is in the Python path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
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

# --- Validation Helper ---

def validate_number_length(input_number: str, output_tensor: Any) -> bool:
    """
    Validates that the output from the relation-based imperative sequence correctly
    finds the length of the input number.
    
    Args:
        input_number: The original number as a string
        output_tensor: The tensor output from the agent containing the length
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Extract the result string from the nested tensor structure
        result_str = str(output_tensor)
        
        # Navigate through the nested structure to find the actual string
        if isinstance(output_tensor, (list, tuple)):
            def find_string_in_nested(obj):
                if isinstance(obj, str):
                    return obj
                elif isinstance(obj, (list, tuple)) and len(obj) > 0:
                    return find_string_in_nested(obj[0])
                else:
                    return str(obj)
            
            result_str = find_string_in_nested(output_tensor)
        
        # Remove the %(...) wrapper if present
        if result_str.startswith("%(") and result_str.endswith(")"):
            result_str = result_str[2:-1]
        
        print(f"📊 Input number: {input_number} (length: {len(input_number)})")
        print(f"📊 Raw output: {result_str}")
        
        # Try to parse as JSON first (relation format)
        try:
            length_list = json.loads(result_str)
            
            # Validate the structure
            if not isinstance(length_list, list):
                print(f"📊 JSON parsing failed, trying simple integer format")
                raise json.JSONDecodeError("Not a list", result_str, 0)
            
            print(f"📊 Output breakdown: {len(length_list)} items")
            
            # Extract the length value
            if len(length_list) != 1:
                print(f"❌ Expected 1 item, got {len(length_list)}")
                return False
            
            length_item = length_list[0]
            if not isinstance(length_item, dict):
                print(f"❌ Invalid item structure: {length_item}")
                return False
            
            # Handle both possible field names
            length_key = 'number_length' if 'number_length' in length_item else 'length'
            if length_key not in length_item:
                print(f"❌ Missing required field '{length_key}' in item: {length_item}")
                return False
            
            reported_length = length_item[length_key]
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to parse as simple integer
            print("📊 JSON parsing failed, trying simple integer format")
            try:
                reported_length = result_str.strip()
            except:
                print(f"❌ Failed to parse output as integer: {result_str}")
                return False
        
        # Convert to integer for comparison
        try:
            reported_length_int = int(reported_length)
        except (ValueError, TypeError):
            print(f"❌ Invalid length value: {reported_length}")
            return False
        
        expected_length = len(input_number)
        
        print(f"📊 Expected length: {expected_length}")
        print(f"📊 Reported length: {reported_length_int}")
        
        if reported_length_int != expected_length:
            print(f"❌ Length mismatch: expected {expected_length}, got {reported_length_int}")
            return False
        
        print(f"✅ Validation passed! Successfully found length {reported_length_int} for number {input_number}")
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


# --- Demo Setup ---

def _build_demo_concepts(number_to_measure: str = "123") -> tuple[Concept, List[Concept], Concept]:
    """Builds the concepts needed for the number length demo."""
    logger = logging.getLogger(__name__)
    logger.info("Building demo concepts for number length")

    # Input concept: The number to measure
    ref_num1 = Reference(axes=["num1"], shape=(1,))
    ref_num1.set(number_to_measure, num1=0)
    logger.info(f"ref_num1: {ref_num1.tensor}")
    concept_num1 = Concept(name="number 1", context="The number to measure", reference=ref_num1, type="{}")

    # Concept for the output length
    ref_length = Reference(axes=["length"], shape=(1,))
    ref_length.set("The length of the number", length=0)  # Will be filled by the agent
    concept_length = Concept(name="number length", context="The number of digits in the number", reference=ref_length, type="{}")

    # Function concept for finding the length
    normcode_string = "::(count all {2}?<$({number length})%_> for {1}?<$({number 1})%_>)"
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set(normcode_string, f=0)
    function_concept = Concept(name=normcode_string, context="Count the digits in a number", type="::", reference=ref_f)
    logger.info(f"ref_f: {ref_f.tensor}")

    # The concept to be inferred, which will hold the length
    concept_to_infer = Concept(name="number_length_result", context="The length of the number", type="{}")
    
    return concept_to_infer, [concept_num1, concept_length], function_concept


def _build_demo_working_interpretation() -> Dict[str, Any]:
    """Builds the working interpretation, enabling the relation output mode."""
    normcode_string = "::(count all {2}?<$({number length})%_> for {1}?<$({number 1})%_>)"
    return {
        "is_relation_output": False,
        normcode_string: {
            "value_order": {
                "number 1": 0,
                "number length": 1
            }
        }
    }


# --- Main Execution ---

def run_number_length_sequence() -> BaseStates:
    """Runs the full imperative sequence to find the length of a number."""
    num = "26897986303456783"
    concept_to_infer, value_concepts, function_concept = _build_demo_concepts(number_to_measure=num)

    inference = Inference(
        "imperative",
        concept_to_infer,
        value_concepts,
        function_concept,
    )

    # The working_interpretation is passed to the AgentFrame to trigger the relational logic
    agent = AgentFrame("demo", working_interpretation=_build_demo_working_interpretation(), body=Body())

    agent.configure(inference, "imperative")

    states = inference.execute()

    # Print the final output from the 'OR' step
    final_ref = states.get_reference("inference", "OR")
    if isinstance(final_ref, Reference):
        logger = logging.getLogger(__name__)
        logger.info("--- Final Output (OR) ---")
        logger.info(f"Axes: {final_ref.axes}")
        logger.info(f"Shape: {final_ref.shape}")
        logger.info(f"Tensor: {final_ref.tensor}")
        # Also print to stdout for clarity
        print("--- Final Output (OR) ---")
        print(f"Axes: {final_ref.axes}")
        print(f"Shape: {final_ref.shape}")
        print(f"Tensor: {final_ref.tensor}")
        
        # Validate the output
        print("\n--- Validation ---")
        validation_result = validate_number_length(num, final_ref.tensor)
        if validation_result:
            print("🎉 All tests passed!")
        else:
            print("💥 Validation failed!")

    return states


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    run_number_length_sequence() 