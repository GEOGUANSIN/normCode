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

def validate_number_breakdown(input_number: str, output_tensor: Any) -> bool:
    """
    Validates that the output from the relation-based imperative sequence correctly
    breaks down the input number into digits and their positions.
    
    Args:
        input_number: The original number as a string
        output_tensor: The tensor output from the agent containing the breakdown
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Extract the result string from the nested tensor structure
        result_str = str(output_tensor)
        
        # Navigate through the nested structure to find the actual string
        # The tensor structure is: [[[[['%([...])']]]]]
        # We need to extract the innermost string
        if isinstance(output_tensor, (list, tuple)):
            # Recursively find the string in nested structures
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
        
        # Parse the JSON list of dictionaries
        breakdown_list = json.loads(result_str)
        
        # Validate the structure
        if not isinstance(breakdown_list, list):
            print(f"❌ Output is not a list: {type(breakdown_list)}")
            return False
        
        print(f"📊 Input number: {input_number} (length: {len(input_number)})")
        print(f"📊 Output breakdown: {len(breakdown_list)} positions")
        
        # Create a mapping of position -> digit from the output
        output_mapping = {}
        for item in breakdown_list:
            if not isinstance(item, dict):
                print(f"❌ Invalid item structure: {item}")
                return False
            
            # Handle both old format ('digit') and new format ('digit_in_position')
            digit_key = 'digit_in_position' if 'digit_in_position' in item else 'digit'
            if digit_key not in item or 'position' not in item:
                print(f"❌ Missing required fields in item: {item}")
                return False
            
            digit = item[digit_key]
            position = item['position']
            
            # Convert to integers for comparison
            try:
                digit_int = int(digit)
                position_int = int(position)
            except (ValueError, TypeError):
                print(f"❌ Invalid digit or position value: digit={digit}, position={position}")
                return False
            
            output_mapping[position_int] = digit_int
        
        # Validate against the input number
        input_digits = list(input_number)
        input_digits.reverse()  # Reverse to match position numbering (1-based from right)
        
        print(f"📊 Expected positions: {len(input_digits)} (1-based from right)")
        print(f"📊 Actual positions: {len(output_mapping)}")
        
        # Check for missing positions
        missing_positions = []
        for i, expected_digit in enumerate(input_digits, 1):
            expected_digit_int = int(expected_digit)
            
            if i not in output_mapping:
                missing_positions.append(i)
                print(f"❌ Missing position {i} (expected digit: {expected_digit_int})")
            else:
                actual_digit = output_mapping[i]
                if actual_digit != expected_digit_int:
                    print(f"❌ Position {i}: expected {expected_digit_int}, got {actual_digit}")
                    return False
        
        if missing_positions:
            print(f"❌ Missing {len(missing_positions)} positions: {missing_positions}")
            return False
        
        # Check for extra positions
        max_expected_position = len(input_digits)
        extra_positions = []
        for position in output_mapping:
            if position > max_expected_position:
                extra_positions.append(position)
                print(f"❌ Extra position {position} in output (max expected: {max_expected_position})")
        
        if extra_positions:
            print(f"❌ Extra {len(extra_positions)} positions: {extra_positions}")
            return False
        
        print(f"✅ Validation passed! Successfully broke down {input_number} into {len(breakdown_list)} digit-position pairs")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON output: {e}")
        print(f"Raw output: {output_tensor}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


# --- Demo Setup ---

def _build_demo_concepts(number_to_break_down: int = 123) -> tuple[Concept, List[Concept], Concept]:
    """Builds the concepts needed for the relation-based imperative demo."""
    logger = logging.getLogger(__name__)
    logger.info("Building demo concepts for relation imperative")

    # Input concept: The number to be broken down
    ref_num1 = Reference(axes=["num1"], shape=(1,))
    ref_num1.set(number_to_break_down, num1=0)
    logger.info(f"ref_num1: {ref_num1.tensor}")
    concept_num1 = Concept(name="number 1", context="The number to break down", reference=ref_num1, type="{}")

    # Concepts for the output relation parts (initially empty)
    ref_digit = Reference(axes=["digit"], shape=(1,))
    ref_digit.set("A digit from the number", digit=0)  # Will be filled by the agent
    concept_digit = Concept(name="digit in position", context="A digit from the number", reference=ref_digit, type="{}")
    
    ref_position = Reference(axes=["position"], shape=(1,))
    ref_position.set("The position of the digit (from the right)", position=0)  # Will be filled by the agent
    concept_position = Concept(name="position", context="The position of the digit (from the right)", reference=ref_position, type="{}")

    # Function concept with multiple '?' marked outputs for the relation
    normcode_string = "::(enumerate all the {2}?<$({digit in position})%_> and {3}?<$({position})%_> from the rightmost digit to the leftmost digit, for {1}?<$({number 1})%_>)"
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set(normcode_string, f=0)
    function_concept = Concept(name=normcode_string, context="Break down a number into its digits and their positions", type="::", reference=ref_f)
    logger.info(f"ref_f: {ref_f.tensor}")

    # The concept to be inferred, which will hold the relational output
    concept_to_infer = Concept(name="number_position_breakdown", context="The digits and their positions in the number", type="{}")
    
    return concept_to_infer, [concept_num1, concept_digit, concept_position], function_concept


def _build_demo_working_interpretation() -> Dict[str, Any]:
    """Builds the working interpretation, enabling the relation output mode."""
    normcode_string = "::(find all {2}?<$({digit in position})%_> and {3}?<$({position})%_> from the rightmost digit to the leftmost digit, for {1}?<$({number 1})%_>)"
    return {
        "is_relation_output": True,
        normcode_string: {
            "value_order": {
                "number 1": 0,
                "digit in position": 1,
                "position": 2
            }
        }
    }


# --- Main Execution ---

def run_relation_imperative_sequence() -> BaseStates:
    """Runs the full imperative sequence with relation-based prompts."""
    num = "26897986303"
    concept_to_infer, value_concepts, function_concept = _build_demo_concepts(number_to_break_down=num)

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
        validation_result = validate_number_breakdown(num, final_ref.tensor)
        if validation_result:
            print("🎉 All tests passed!")
        else:
            print("💥 Validation failed!")

    return states


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    run_relation_imperative_sequence() 