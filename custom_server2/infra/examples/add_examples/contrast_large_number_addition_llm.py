import json
import logging
import os
import sys
import random

# Ensure the project root is in the Python path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import core components
try:
	from infra._agent._models._language_models import LanguageModel
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
	from infra._agent._models._language_models import LanguageModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def generate_number_pair(min_length: int = 10, max_length: int = 20) -> tuple[str, str]:
    """
    Generate a pair of random numbers with lengths within the specified range.
    
    Args:
        min_length: Minimum length for each number
        max_length: Maximum length for each number
        
    Returns:
        A tuple of two random number strings
    """
    length1 = random.randint(min_length, max_length)
    length2 = random.randint(min_length, max_length)
    
    return generate_random_number(length1), generate_random_number(length2)

def add_large_numbers_with_llm(llm: LanguageModel, num1: str, num2: str) -> dict:
    """
    Asks a large language model to add two large numbers and returns the structured response.

    Args:
        llm: An instance of the LanguageModel class.
        num1: The first large number as a string.
        num2: The second large number as a string.

    Returns:
        A dictionary containing the LLM's reasoning and answer.
    """
    prompt = f"""
    Think step by step to add the following two large numbers:
    Number 1: {num1}
    Number 2: {num2}

    Output your response in a single JSON object with two keys:
    1. "reasoning": A string explaining the step-by-step process you used for the addition.
    2. "answer": The final sum as a string.
    """
    
    response_str = llm.generate(
        prompt=prompt,
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response_str)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON response from LLM: {response_str}")
        return {
            "reasoning": "Error: Failed to parse JSON response from LLM.",
            "answer": "0"
        }

def run_addition_test(llm: LanguageModel, num1: str, num2: str, test_name: str = "Test") -> bool:
    """
    Run a single addition test and display the results.
    
    Args:
        llm: The language model instance
        num1: First number to add
        num2: Second number to add
        test_name: Name for this test case
        
    Returns:
        True if the LLM got the answer correct, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"                    {test_name}")
    print(f"{'='*60}")
    
    print(f"Number 1: {num1} (length: {len(num1)})")
    print(f"Number 2: {num2} (length: {len(num2)})")
    
    # Get the LLM's answer
    llm_response = add_large_numbers_with_llm(llm, num1, num2)
    llm_answer = llm_response.get("answer", "0")
    llm_reasoning = llm_response.get("reasoning", "No reasoning provided.")

    # Calculate the correct answer locally
    correct_answer = str(int(num1) + int(num2))

    print(f"\n🤖 LLM's Reasoning:")
    print(llm_reasoning)
    
    print(f"\n{'-'*50}")
    print(f"🧮 LLM's Answer:      {llm_answer}")
    print(f"✅ Correct Answer:    {correct_answer}")
    print(f"{'-'*50}")
    
    is_correct = llm_answer == correct_answer
    if is_correct:
        print("🎉 The LLM's answer is correct!")
    else:
        print("💥 The LLM's answer is incorrect.")
        
    return is_correct

if __name__ == "__main__":
    # Initialize the language model
    llm = LanguageModel("qwen-plus")

    # # Test 1: Fixed numbers (from your original example)
    # number_1 = "890826897986303343456"
    # number_2 = "2374839283767523943"
    # run_addition_test(llm, number_1, number_2, "Fixed Numbers Test")
    
    # Test 2: Auto-generated numbers (medium length)
    print(f"\n{'='*60}")
    print("           Generating Random Numbers...")
    print(f"{'='*60}")
    
    num1_auto, num2_auto = generate_number_pair(min_length=24, max_length=30)
    run_addition_test(llm, num1_auto, num2_auto, "Auto-Generated Numbers Test")
    
    # # Test 3: Very large numbers
    # num1_large, num2_large = generate_number_pair(min_length=25, max_length=30)
    # run_addition_test(llm, num1_large, num2_large, "Very Large Numbers Test")
    
    print(f"\n{'='*60}")
    print("           Test Summary")
    print(f"{'='*60}")
    print("All tests completed. Check the results above for accuracy.") 