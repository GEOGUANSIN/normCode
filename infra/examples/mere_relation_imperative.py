import os
import sys
import logging
from typing import Any, Dict, List
import json
import ast

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
    Handles both correct JSON output and malformed list-of-strings output.
    """
    try:
        breakdown_list = []

        # Helper to extract the innermost list from a nested list structure
        def get_innermost_list(obj):
            current = obj
            while isinstance(current, list) and len(current) > 0 and isinstance(current[0], list):
                current = current[0]
            return current if isinstance(current, list) else None

        # Helper to extract a single string from a nested list structure
        def get_innermost_string(obj):
            current = obj
            while isinstance(current, list) and len(current) > 0:
                current = current[0]
            return current if isinstance(current, str) else None

        string_list = get_innermost_list(output_tensor)
        json_string = get_innermost_string(output_tensor)

        if string_list and isinstance(string_list[0], str) and string_list[0].startswith("%("):
            # Case 1: Malformed list of strings like ["%({'k':'v'})", ...]
            print("ℹ️  Detected list-of-strings format. Parsing with 'ast.literal_eval'.")
            for item_str in string_list:
                if item_str.startswith("%(") and item_str.endswith(")"):
                    item_str = item_str[2:-1]
                try:
                    item_dict = ast.literal_eval(item_str)
                    breakdown_list.append(item_dict)
                except (ValueError, SyntaxError) as e:
                    print(f"❌ Failed to parse item string: '{item_str}'. Error: {e}")
                    return False
        
        elif json_string:
            # Case 2: Correct single JSON string
            print("ℹ️  Detected single-string format. Parsing as JSON.")
            if json_string.startswith("%(") and json_string.endswith(")"):
                json_string = json_string[2:-1]
            
            try:
                parsed_json = json.loads(json_string)
                if isinstance(parsed_json, dict) and "output" in parsed_json:
                    print("ℹ️  Extracted 'output' key from thinking-enabled JSON.")
                    breakdown_list = parsed_json["output"]
                else:
                    breakdown_list = parsed_json # Assumes a simple list of dicts
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON output: {e}")
                print(f"Raw output: {output_tensor}")
                return False
        else:
            print(f"❌ Output tensor is not in a recognized format.")
            print(f"Raw output: {output_tensor}")
            return False

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
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


# --- Demo Setup ---

def _build_demo_concepts(number_to_break_down: int = 123, normcode_string: str = "::(enumerate all the {2}?<$({digit in position})%_> and {3}?<$({position})%_> from the rightmost digit to the leftmost digit, for {1}?<$({number 1})%_>)" ) -> tuple[Concept, List[Concept], Concept]:
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
    ref_digit.set("one of 0, 1, 2, 3, 4, 5, 6, 7, 8, 9", digit=0)  # Will be filled by the agent
    concept_digit = Concept(name="digit in position", context="A digit from the number", reference=ref_digit, type="{}")
    
    ref_position = Reference(axes=["position"], shape=(1,))
    ref_position.set("starting with position 1", position=0)  # Will be filled by the agent
    concept_position = Concept(name="position", context="The position of the digit (from the right)", reference=ref_position, type="{}")

    # Function concept with multiple '?' marked outputs for the relation
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set(normcode_string, f=0)
    function_concept = Concept(name=normcode_string, context="Break down a number into its digits and their positions", type="::", reference=ref_f)
    logger.info(f"ref_f: {ref_f.tensor}")

    # The concept to be inferred, which will hold the relational output
    concept_to_infer = Concept(name="number digit position pairs", context="The digits and their positions in the number", type="{}")
    
    return concept_to_infer, [concept_num1, concept_digit, concept_position], function_concept


def _build_demo_working_interpretation(normcode_string: str = "::(enumerate all the {2}?<$({digit in position})%_> and {3}?<$({position})%_> from the rightmost digit to the leftmost digit, for {1}?<$({number 1})%_>)" ) -> Dict[str, Any]:
    """Builds the working interpretation, enabling the relation output mode."""
    return {
        "is_relation_output": True,
        "with_thinking": True,
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
    num = "20941565794707318456987069"
    normcode_string = "::(Given a {1}<$({number})%_>, annotate from rightmost to leftmost all the {2}?<$({digit in position})%_> and {3}?<$({position})%_> pairs in {1}<$({number})%_>)"
    normcode_string = normcode_string.replace("$len$", str(len(num)))
    concept_to_infer, value_concepts, function_concept = _build_demo_concepts(number_to_break_down=num, normcode_string=normcode_string)

    inference = Inference(
        "imperative",
        concept_to_infer,
        function_concept,
        value_concepts,
    )

    # The working_interpretation is passed to the AgentFrame to trigger the relational logic
    body=Body(llm_name="qwen-turbo-latest")

    agent = AgentFrame("demo", working_interpretation=_build_demo_working_interpretation(normcode_string=normcode_string), body=body)

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