import os
import sys
import logging
from typing import Any, Dict, List
import json
import random

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

# --- Random Number Generation for Testing ---

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

# --- Validation Helper ---

def validate_last_digit(input_number: str, output_tensor: Any) -> bool:
    """
    Validates that the output from the relation-based imperative sequence correctly
    finds the last digit of the input number.
    
    Args:
        input_number: The original number as a string
        output_tensor: The tensor output from the agent containing the last digit
        
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
            last_digit_list = json.loads(result_str)
            
            # Validate the structure
            if not isinstance(last_digit_list, list):
                print(f"📊 JSON parsing failed, trying simple string format")
                raise json.JSONDecodeError("Not a list", result_str, 0)
            
            print(f"📊 Output breakdown: {len(last_digit_list)} items")
            
            # Extract the last digit value
            if len(last_digit_list) != 1:
                print(f"❌ Expected 1 item, got {len(last_digit_list)}")
                return False
            
            last_digit_item = last_digit_list[0]
            
            # Handle both dictionary format and direct value format
            if isinstance(last_digit_item, dict):
                # Dictionary format with field names
                last_digit_key = 'last_digit' if 'last_digit' in last_digit_item else 'digit'
                if last_digit_key not in last_digit_item:
                    print(f"❌ Missing required field '{last_digit_key}' in item: {last_digit_item}")
                    return False
                reported_last_digit = last_digit_item[last_digit_key]
            else:
                # Direct value format (the item is the last digit itself)
                reported_last_digit = str(last_digit_item)
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to parse as simple string
            print("📊 JSON parsing failed, trying simple string format")
            reported_last_digit = result_str.strip()
            
            # Handle case where the string might be a list representation
            if reported_last_digit.startswith('[') and reported_last_digit.endswith(']'):
                # Remove brackets and extract the content
                content = reported_last_digit[1:-1].strip()
                # Remove quotes if present
                if content.startswith("'") and content.endswith("'"):
                    content = content[1:-1]
                elif content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]
                reported_last_digit = content
        
        # Remove quotes if present
        if reported_last_digit.startswith('"') and reported_last_digit.endswith('"'):
            reported_last_digit = reported_last_digit[1:-1]
        
        # Get the expected last digit using string indexing (no integer conversion needed)
        expected_last_digit = input_number[-1]  # Python string last character
        
        print(f"📊 Expected last digit: {expected_last_digit}")
        print(f"📊 Reported last digit: {reported_last_digit}")
        
        if reported_last_digit != expected_last_digit:
            print(f"❌ Last digit mismatch: expected {expected_last_digit}, got {reported_last_digit}")
            return False
        
        print(f"✅ Validation passed! Successfully found last digit {reported_last_digit} for number {input_number} (length: {len(input_number)})")
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


def validate_number_without_unit_place(input_number: str, output_tensor: Any) -> bool:
    """
    Validates that the output from the second inference correctly removes the unit place digit
    from the input number, resulting in a shorter number.
    
    Args:
        input_number: The original number as a string
        output_tensor: The tensor output from the agent containing the number without unit place
        
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
            number_list = json.loads(result_str)
            
            # Validate the structure
            if not isinstance(number_list, list):
                print(f"📊 JSON parsing failed, trying simple string format")
                raise json.JSONDecodeError("Not a list", result_str, 0)
            
            print(f"📊 Output breakdown: {len(number_list)} items")
            
            # Extract the number value
            if len(number_list) != 1:
                print(f"❌ Expected 1 item, got {len(number_list)}")
                return False
            
            number_item = number_list[0]
            
            # Handle both dictionary format and direct value format
            if isinstance(number_item, dict):
                # Dictionary format with field names
                number_key = 'number' if 'number' in number_item else 'result'
                if number_key not in number_item:
                    print(f"❌ Missing required field '{number_key}' in item: {number_item}")
                    return False
                reported_number = number_item[number_key]
            else:
                # Direct value format (the item is the number itself)
                reported_number = str(number_item)
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to parse as simple string
            print("📊 JSON parsing failed, trying simple string format")
            reported_number = result_str.strip()
            
            # Handle case where the string might be a list representation
            if reported_number.startswith('[') and reported_number.endswith(']'):
                # Remove brackets and extract the content
                content = reported_number[1:-1].strip()
                # Remove quotes if present
                if content.startswith("'") and content.endswith("'"):
                    content = content[1:-1]
                elif content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]
                reported_number = content
        
        # Remove quotes if present
        if reported_number.startswith('"') and reported_number.endswith('"'):
            reported_number = reported_number[1:-1]
        
        # Get the expected number without unit place using string slicing (no integer conversion needed)
        expected_number = input_number[:-1]  # Python string without last character
        
        print(f"📊 Expected number without unit place: {expected_number} (length: {len(expected_number)})")
        print(f"📊 Reported number: {reported_number} (length: {len(reported_number)})")
        
        if reported_number != expected_number:
            print(f"❌ Number mismatch: expected {expected_number}, got {reported_number}")
            return False
        
        if len(reported_number) != len(input_number) - 1:
            print(f"❌ Length mismatch: expected {len(input_number) - 1}, got {len(reported_number)}")
            return False
        
        print(f"✅ Validation passed! Successfully removed unit place digit. Result: {reported_number} (length: {len(reported_number)})")
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


# --- Demo Setup ---

def _build_demo_concepts(number_to_analyze: str = "123", normcode_string: str = "::(get last {2}?<$({last digit})%_> from {1}<$({number 1})%_>)" ) -> tuple[Concept, List[Concept], Concept]:
    """Builds the concepts needed for the last digit demo."""
    logger = logging.getLogger(__name__)
    logger.info("Building demo concepts for last digit extraction")

    # Input concept: The number to analyze
    ref_num1 = Reference(axes=["num1"], shape=(1,))
    ref_num1.set(number_to_analyze, num1=0)
    logger.info(f"ref_num1: {ref_num1.tensor}")
    concept_num1 = Concept(name="number 1", context="The number to find the last digit of", reference=ref_num1, type="{}")

    # Concept for the output last digit
    ref_last_digit = Reference(axes=["last_digit"], shape=(1,))
    ref_last_digit.set("1 digit counting from the right", last_digit=0)  # Will be filled by the agent
    concept_last_digit = Concept(name="last digit", context="The rightmost digit of the number", reference=ref_last_digit, type="{}")

    # Function concept for getting the last digit
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set(normcode_string, f=0)
    function_concept = Concept(name=normcode_string, context="Get the last digit of a number", type="::", reference=ref_f)
    logger.info(f"ref_f: {ref_f.tensor}")

    # The concept to be inferred, which will hold the last digit
    concept_to_infer = Concept(name="unit place digit", context="The unit place digit of the number", type="{}")
    
    return concept_to_infer, [concept_num1, concept_last_digit], function_concept


def _build_remove_unit_place_concepts(number_to_analyze: str = "123", normcode_string: str = "::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)" ) -> tuple[Concept, List[Concept], Concept]:
    """Builds the concepts needed for removing the unit place digit demo."""
    logger = logging.getLogger(__name__)
    logger.info("Building demo concepts for removing unit place digit")

    # Input concept: The number to analyze
    ref_number = Reference(axes=["number"], shape=(1,))
    ref_number.set(number_to_analyze, number=0)
    logger.info(f"ref_number: {ref_number.tensor}")
    concept_number = Concept(name="number", context="The number to remove the unit place digit from", reference=ref_number, type="{}")

    # Concept for the unit place digit to remove
    ref_unit_place = Reference(axes=["unit_place"], shape=(1,))
    ref_unit_place.set("the rightmost digit", unit_place=0)  # Will be filled by the agent
    concept_unit_place = Concept(name="unit place digit", context="The rightmost digit to be removed", reference=ref_unit_place, type="{}")

    # Function concept for removing the unit place digit
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set(normcode_string, f=0)
    function_concept = Concept(name=normcode_string, context="Remove the unit place digit from a number", type="::", reference=ref_f)
    logger.info(f"ref_f: {ref_f.tensor}")

    # The concept to be inferred, which will hold the number without unit place
    concept_to_infer = Concept(name="number without unit place", context="The number with the unit place digit removed", type="{}")
    
    return concept_to_infer, [concept_number, concept_unit_place], function_concept


def _build_demo_working_interpretation(normcode_string: str = "::(get last {2}?<$({last digit})%_> from {1}?<$({number 1})%_>)" ) -> Dict[str, Any]:
    """Builds the working interpretation, enabling the relation output mode."""
    return {
        "is_relation_output": False,
        "with_thinking": True,
        normcode_string: {
            "value_order": {
                "number 1": 0,
                "last digit": 1
            }
        }
    }


def _build_remove_unit_place_working_interpretation(normcode_string: str = "::(remove {2}?<$({unit place digit})%_> from {1}?<$({number})%_>)" ) -> Dict[str, Any]:
    """Builds the working interpretation for removing unit place digit."""
    return {
        "is_relation_output": False,
        "with_thinking": True,
        normcode_string: {
            "value_order": {
                "number": 0,
                "unit place digit": 1
            }
        }
    }


# --- Main Execution ---

def run_last_digit_sequence() -> BaseStates:
    """Runs the full imperative sequence to find the last digit of a number."""
    num = "26897986303456783223423423456098765434678900987653467890087654323467543212098765434567890987654"
    normcode_string = "::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)"
    concept_to_infer, value_concepts, function_concept = _build_demo_concepts(number_to_analyze=num, normcode_string=normcode_string)

    inference = Inference(
        "imperative",
        concept_to_infer,
        function_concept,
        value_concepts,
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
        validation_result = validate_last_digit(num, final_ref.tensor)
        if validation_result:
            print("🎉 All tests passed!")
        else:
            print("💥 Validation failed!")

    return states


def run_last_digit_sequence_with_number(input_number: str) -> BaseStates:
    """Runs the full imperative sequence to find the last digit of a given number."""
    normcode_string = "::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)"
    concept_to_infer, value_concepts, function_concept = _build_demo_concepts(number_to_analyze=input_number, normcode_string=normcode_string)

    inference = Inference(
        "imperative",
        concept_to_infer,
        function_concept,
        value_concepts,
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

    return states


def run_remove_unit_place_sequence() -> BaseStates:
    """Runs the full imperative sequence to remove the unit place digit from a number."""
    num = "26897986303456783223423423456098765434678900987653467890087654323467543212098765434567890987654"
    normcode_string = "::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)"
    concept_to_infer, value_concepts, function_concept = _build_remove_unit_place_concepts(number_to_analyze=num, normcode_string=normcode_string)

    inference = Inference(
        "imperative",
        concept_to_infer,
        function_concept,
        value_concepts,
    )

    # The working_interpretation is passed to the AgentFrame to trigger the relational logic
    agent = AgentFrame("demo", working_interpretation=_build_remove_unit_place_working_interpretation(normcode_string=normcode_string), body=Body())

    agent.configure(inference, "imperative")

    states = inference.execute()

    # Print the final output from the 'OR' step
    final_ref = states.get_reference("inference", "OR")
    if isinstance(final_ref, Reference):
        logger = logging.getLogger(__name__)
        logger.info("--- Final Output (OR) - Remove Unit Place ---")
        logger.info(f"Axes: {final_ref.axes}")
        logger.info(f"Shape: {final_ref.shape}")
        logger.info(f"Tensor: {final_ref.tensor}")
        # Also print to stdout for clarity
        print("--- Final Output (OR) - Remove Unit Place ---")
        print(f"Axes: {final_ref.axes}")
        print(f"Shape: {final_ref.shape}")
        print(f"Tensor: {final_ref.tensor}")
        
        # Validate the output
        print("\n--- Validation - Remove Unit Place ---")
        validation_result = validate_number_without_unit_place(num, final_ref.tensor)
        if validation_result:
            print("🎉 All tests passed!")
        else:
            print("💥 Validation failed!")

    return states


def run_remove_unit_place_sequence_with_number(input_number: str) -> BaseStates:
    """Runs the full imperative sequence to remove the unit place digit from a given number."""
    normcode_string = "::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)"
    concept_to_infer, value_concepts, function_concept = _build_remove_unit_place_concepts(number_to_analyze=input_number, normcode_string=normcode_string)

    inference = Inference(
        "imperative",
        concept_to_infer,
        function_concept,
        value_concepts,
    )

    # The working_interpretation is passed to the AgentFrame to trigger the relational logic
    agent = AgentFrame("demo", working_interpretation=_build_remove_unit_place_working_interpretation(normcode_string=normcode_string), body=Body())

    agent.configure(inference, "imperative")

    states = inference.execute()

    # Print the final output from the 'OR' step
    final_ref = states.get_reference("inference", "OR")
    if isinstance(final_ref, Reference):
        logger = logging.getLogger(__name__)
        logger.info("--- Final Output (OR) - Remove Unit Place ---")
        logger.info(f"Axes: {final_ref.axes}")
        logger.info(f"Shape: {final_ref.shape}")
        logger.info(f"Tensor: {final_ref.tensor}")
        # Also print to stdout for clarity
        print("--- Final Output (OR) - Remove Unit Place ---")
        print(f"Axes: {final_ref.axes}")
        print(f"Shape: {final_ref.shape}")
        print(f"Tensor: {final_ref.tensor}")

    return states


def run_both_inferences() -> tuple[BaseStates, BaseStates]:
    """Runs both inferences: first to get the last digit, then to remove it."""
    print("=" * 80)
    print("🔍 INFERENCE 1: Finding the last digit")
    print("=" * 80)
    
    # First inference: get the last digit
    states1 = run_last_digit_sequence()
    
    print("\n" + "=" * 80)
    print("🔍 INFERENCE 2: Removing the unit place digit")
    print("=" * 80)
    
    # Second inference: remove the unit place digit
    states2 = run_remove_unit_place_sequence()
    
    return states1, states2


def run_both_inferences_with_number(input_number: str) -> tuple[BaseStates, BaseStates]:
    """Runs both inferences with a given number: first to get the last digit, then to remove it."""
    print("=" * 80)
    print(f"🔍 INFERENCE 1: Finding the last digit of {input_number}")
    print("=" * 80)
    
    # First inference: get the last digit
    states1 = run_last_digit_sequence_with_number(input_number)
    
    print("\n" + "=" * 80)
    print(f"🔍 INFERENCE 2: Removing the unit place digit from {input_number}")
    print("=" * 80)
    
    # Second inference: remove the unit place digit
    states2 = run_remove_unit_place_sequence_with_number(input_number)
    
    return states1, states2


def run_both_inferences_with_number_and_validation(input_number: str) -> tuple[BaseStates, BaseStates, bool, bool]:
    """Runs both inferences with a given number and returns validation results."""
    print("=" * 80)
    print(f"🔍 INFERENCE 1: Finding the last digit of {input_number}")
    print("=" * 80)
    
    # First inference: get the last digit
    states1 = run_last_digit_sequence_with_number(input_number)
    
    # Get validation result for first inference
    final_ref1 = states1.get_reference("inference", "OR")
    validation1 = False
    if isinstance(final_ref1, Reference):
        validation1 = validate_last_digit(input_number, final_ref1.tensor)
    
    print("\n" + "=" * 80)
    print(f"🔍 INFERENCE 2: Removing the unit place digit from {input_number}")
    print("=" * 80)
    
    # Second inference: remove the unit place digit
    states2 = run_remove_unit_place_sequence_with_number(input_number)
    
    # Get validation result for second inference
    final_ref2 = states2.get_reference("inference", "OR")
    validation2 = False
    if isinstance(final_ref2, Reference):
        validation2 = validate_number_without_unit_place(input_number, final_ref2.tensor)
    
    # Log combined validation results
    print("\n" + "=" * 80)
    print("📊 PIPELINE VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Input number: {input_number} (length: {len(input_number)})")
    print(f"Last digit extraction: {'✅ PASSED' if validation1 else '❌ FAILED'}")
    print(f"Unit place removal: {'✅ PASSED' if validation2 else '❌ FAILED'}")
    
    if validation1 and validation2:
        print("🎉 Both inferences passed validation!")
    elif validation1 or validation2:
        print("⚠️  One inference passed, one failed")
    else:
        print("💥 Both inferences failed validation!")
    
    print("=" * 80)
    
    return states1, states2, validation1, validation2


def run_test_with_random_numbers(length: int = 4000) -> tuple[BaseStates, BaseStates]:
    """Runs both inferences with a randomly generated number of specified length."""
    test_number = generate_random_number(length)
    print(f"🎲 Generated test number: {test_number} (length: {len(test_number)})")
    return run_both_inferences_with_number_and_validation(test_number)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    run_test_with_random_numbers() 