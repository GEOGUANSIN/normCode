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

def validate_number_reverse(input_number: str, output_tensor: Any) -> bool:
    """
    Validates that the output from the relation-based imperative sequence correctly
    reverses the input number.
    
    Args:
        input_number: The original number as a string
        output_tensor: The tensor output from the agent containing the reversed number
        
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
            reverse_list = json.loads(result_str)
            
            # Validate the structure
            if not isinstance(reverse_list, list):
                print(f"📊 JSON parsing failed, trying simple string format")
                raise json.JSONDecodeError("Not a list", result_str, 0)
            
            print(f"📊 Output breakdown: {len(reverse_list)} items")
            
            # Extract the reversed number value
            if len(reverse_list) != 1:
                print(f"❌ Expected 1 item, got {len(reverse_list)}")
                return False
            
            reverse_item = reverse_list[0]
            
            # Handle both dictionary format and direct value format
            if isinstance(reverse_item, dict):
                # Dictionary format with field names
                reverse_key = 'reversed_number' if 'reversed_number' in reverse_item else 'number'
                if reverse_key not in reverse_item:
                    print(f"❌ Missing required field '{reverse_key}' in item: {reverse_item}")
                    return False
                reported_reverse = reverse_item[reverse_key]
            else:
                # Direct value format (the item is the reversed number itself)
                reported_reverse = str(reverse_item)
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to parse as simple string
            print("📊 JSON parsing failed, trying simple string format")
            reported_reverse = result_str.strip()
            
            # Handle case where the string might be a list representation
            if reported_reverse.startswith('[') and reported_reverse.endswith(']'):
                # Remove brackets and extract the content
                content = reported_reverse[1:-1].strip()
                # Remove quotes if present
                if content.startswith("'") and content.endswith("'"):
                    content = content[1:-1]
                elif content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]
                reported_reverse = content
        
        # Remove quotes if present
        if reported_reverse.startswith('"') and reported_reverse.endswith('"'):
            reported_reverse = reported_reverse[1:-1]
        
        expected_reverse = input_number[::-1]  # Python string reversal
        
        print(f"📊 Expected reversed: {expected_reverse} (length: {len(expected_reverse)})")
        print(f"📊 Reported reversed: {reported_reverse} (length: {len(reported_reverse)})")
        
        if reported_reverse != expected_reverse:
            print(f"❌ Reversal mismatch: expected {expected_reverse}, got {reported_reverse}")
            return False
        
        print(f"✅ Validation passed! Successfully reversed {input_number} (length: {len(input_number)}) to {reported_reverse} (length: {len(reported_reverse)})")
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


# --- Demo Setup ---

def _build_demo_concepts(number_to_reverse: str = "123", normcode_string: str = "::(reverse {1}<$({number 1})%_> to have {2}?<$({reversed number})%_>)" ) -> tuple[Concept, List[Concept], Concept]:
    """Builds the concepts needed for the number reversal demo."""
    logger = logging.getLogger(__name__)
    logger.info("Building demo concepts for number reversal")

    # Input concept: The number to reverse
    ref_num1 = Reference(axes=["num1"], shape=(1,))
    ref_num1.set(number_to_reverse, num1=0)
    logger.info(f"ref_num1: {ref_num1.tensor}")
    concept_num1 = Concept(name="number 1", context="The number to reverse", reference=ref_num1, type="{}")

    # Concept for the output reversed number
    ref_reversed = Reference(axes=["reversed"], shape=(1,))
    ref_reversed.set("The reversed number", reversed=0)  # Will be filled by the agent
    concept_reversed = Concept(name="reversed number", context="The number with digits in reverse order", reference=ref_reversed, type="{}")

    # Function concept for reversing the number
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set(normcode_string, f=0)
    function_concept = Concept(name=normcode_string, context="Reverse the digits in a number", type="::", reference=ref_f)
    logger.info(f"ref_f: {ref_f.tensor}")

    # The concept to be inferred, which will hold the reversed number
    concept_to_infer = Concept(name="reversed_number_result", context="The reversed number", type="{}")
    
    return concept_to_infer, [concept_num1, concept_reversed], function_concept


def _build_demo_working_interpretation(normcode_string: str = "::(reverse {1}<$({number 1})%_> to have {2}?<$({reversed number})%_>)" ) -> Dict[str, Any]:
    """Builds the working interpretation, enabling the relation output mode."""
    return {
        "is_relation_output": False,
        normcode_string: {
            "value_order": {
                "number 1": 0,
                "reversed number": 1
            }
        }
    }


# --- Main Execution ---

def run_number_reverse_sequence() -> BaseStates:
    """Runs the full imperative sequence to reverse a number."""
    num = "268456783"
    normcode_string = "::(reverse {1}<$({number 1})%_> to have {2}?<$({reversed number})%_>)"
    concept_to_infer, value_concepts, function_concept = _build_demo_concepts(number_to_reverse=num, normcode_string=normcode_string)

    inference = Inference(
        "imperative",
        concept_to_infer,
        value_concepts,
        function_concept,
    )

    # The working_interpretation is passed to the AgentFrame to trigger the relational logic
    agent = AgentFrame("demo", working_interpretation=_build_demo_working_interpretation(normcode_string=normcode_string), body=Body())

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
        validation_result = validate_number_reverse(num, final_ref.tensor)
        if validation_result:
            print("🎉 All tests passed!")
        else:
            print("💥 Validation failed!")

    return states


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    run_number_reverse_sequence() 