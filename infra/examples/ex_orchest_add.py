import uuid
import logging
import os
import sys
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import traceback

# --- Infra Imports ---
try:
    from infra import Inference, Concept, AgentFrame, Reference, BaseStates
    from infra._orchest._blackboard import Blackboard
    from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
    from infra._orchest._waitlist import WaitlistItem, Waitlist
    from infra._orchest._tracker import ProcessTracker
    from infra._orchest._orchestrator import Orchestrator
    from infra._loggers.utils import setup_orchestrator_logging
    from infra._agent._body import Body
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))
    from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Blackboard, Body
    from infra._loggers.utils import setup_orchestrator_logging



# --- Normcode for this example ---

failed_count_natural = """
Process a number from right to left: 
at each step, 
extract the rightmost digit with its position, 
then remove that digit. 
Continue until the number is empty."""

Normcode_raw_paragraph_reversed = """
To obtain all pairs of index and digit of two numbers, 
we process the number step by step. In each step, 
we obtain the digit of the step by getting the unit place value of the number,
group the index and digit of the step as a pair,
and collect this pair.
After that, 
we increase the index of the step by one.
and continue with the new number, 
which is obtained by removing the digit of the step from the number,
and stop when the number is single digit.


after obtain the pairs of index and digit of the number,
we process the digit 

"""


Normcode_count_natural_paragraph = """
To obtain all the pairs of index and digit of the number, 
we take the number in a continuous step-by-step process.
For every number in each step of the process, 
we assign the current pair of index and digit to the collection of all the pair of index and digit of the number
The current pair of index and digit is obtained by grouping the current index and current digit as a one-one pair.
Where The current digit is obtained by getting the unit place value of the current leftover number.
and The current index is inherited from the previous step of the process.
After we have obtained the current pairs of index and digit of the number, 
we increment the index by one.
and continue with the new leftover number in the process, 
which is obtained by removing the current digit from the current leftover number, unless the number is single digit, in which case we keep the number to stop the process.
"""

Normcode_count_natural = """
all pairs of index and digit of number | 1. quantifying
    <= for every number and their index in the leftover number collection | 1.1. assigning
        <= assign the current pair of index and digit 
        <- current pair of index and digit | 1.1.2. grouping
            <= group the current index and current digit as a one-to-one pair
            <- the current index
            <- the current digit | 1.1.2.3. imperative
                <= get the unit place value of the current leftover number
                <- the meaning of unit place value
                <- the current leftover number
        <- the leftover number collection | 1.1.3. assigning
            <= add the new leftover number to the leftover number collection
            <- the new leftover number | 1.1.3.2. imperative
                <= if the number is not single digit, then remove the current digit from the current leftover number | 1.1.3.2.1. timing
                     <= after the current pair of index and digit is obtained 
                <- the current leftover number
        <- the current index | 1.1.4. imperative
            <= increase the current index by one | 1.1.4.1. timing
                <= after the current pair of index and digit is obtained 
            <- the current index
    <- the number as the leftover number collection
"""



Normcode_count = """
[all {position} and {position sum} of number pair] | 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1)^[{position}<*1>;{carry-over}<*1>] | 1.1. assigning
        <= $.({residual}*1))

        <- {carry-over number}*1
            <= ::(get the {carry-over number}? of {digit sum})
                <= @after({digit sum}*1)
            <- {carry-over number}?
            <- {digit sum}*1

        <- {residual}*1
            <= ::(get the {residual}? of {digit sum} in base 10)
                <= @after({digit sum}*1)
            <- {residual}?
            <- {digit sum}*1

        <- {digit sum}*1
            <= ::(sum {number} and {carry-over number} to get {sum}?)
            <- {sum}?
            <- {carry-over number}*1
            <- [all {unit place value} of numbers]*1
                <= &in({unit place value}*1:{number})
                <- {unit place value}*1
                    <= *every({number pair}*1)%:[{number}]@(2)
                        <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>) 
                        <- {unit place digit}?<:{2}>
                        <- {number pair}*1*2
                    <- {number pair}*1

        <- {number pair}<:{1}> | 1.1.3. assigning
            <= $+({new number pair}:{number pair})%:[{number pair}] 
            <- {new number pair} | 1.1.3.2. imperative/simple
                <= *every({number pair}*1)%:[{number}]@(2)
                    <= ::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>) 
                        <= @after([{position} and {position sum}]*) | 1.1.3.2.1. timing
                    <- {unit place digit}?<:{2}> 
                    <- {number pair}*1*2
                <- {number pair}*1

        <- {position}*1 | 1.1.4. imperative/simple
            <= ::(increase {1}?<$({position})%_>) by one) | 1.1.4.1. timing
                <= @after([{carry-over number}*1) 
            <- {position}*1
    <- {number pair}



number_pairs%=[
    numbers%=[  
    125, 14
    ],
    [
    12, 1
    ]

]    
"""


# --- Data Definitions ---
def create_sequential_repositories(number: str = "123"):
    """Creates concept and inference repositories for a waitlist scenario with two intermediate data concepts and three functions."""
    # Create concept entries
    concept_entries = [
        # Main concept to be inferred - the result of the quantification
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[all {index} and {digit} of number]",
            axis_name="index and digit pairs",
            context="all index and digit pairs of number",
            type="{}",
            description="Extract all digits from a number with their positions",
            is_final_concept=True,
        ),
        
        # The number to process
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number}",
            type="{}",
            axis_name="number",
            context="the input number to extract digits from",
            description="The input number to extract digits from",
            reference_data=[f"%({number})"],
            reference_axis_names=["number"],
            is_ground_concept=True,
            is_invariant=True
        ),
    
        # The grouping concept for index and digit pairs
            ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[{index} and {digit}]*",
            type="[]",
            axis_name="one pair of index and digit",
            context="one pair of index and digit in the number",
            description="Collection of index-digit pairs",
        ),
        

        # The number concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number}*",
            type="{}",
            axis_name="number",
            context="the number to process under quantifying",
            description="The number to process under quantifying",
        ),

        # The index concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{index}*",
            type="{}",
            axis_name="index",
            context="the current position index in the number",
            description="Current position index in the number",
            reference_data='1',
            reference_axis_names=["index"],
            is_ground_concept=True,
        ),
        
        # The digit concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{digit}*",
            type="{}",
            axis_name="digit",
            context="the digit extracted from the current position",
            description="The digit extracted from the current position",
        ),
        
        # The unit place digit concept (result of get operation)
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{unit place digit}?",
            type="{}",
            axis_name="unit place digit",
            context="the digit extracted from the current position",
            description="The extracted digit from the current position",
            reference_data='1 digit counting from the right',
            reference_axis_names=["unit place digit"],
            is_ground_concept=True,
        ),
        
        # The new number concept (result of remove operation)
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{new number}",
            type="{}",
            axis_name="new number",
            context="the number with the current digit removed",
            description="The number with the current digit removed",
        ),
        
        # The increment function for index
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(increase {1}?<$({index})%_>) by one",
            type="::({})",
            axis_name="increase",
            context="the current position index in the number to increase",
            description="Increment the index counter",
            reference_data='::(increase {1}?<$({index})%_>) by one',
            reference_axis_names=["increase"],
            # is_ground_concept = True,
            is_invariant=True
        ),
        
        # The get digit function
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)",
            type="::({})",
            axis_name="get",
            context="the value of the unit place digit",
            description="Extract the rightmost digit from a number",
            reference_data='::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)',
            reference_axis_names=["get"],
            is_ground_concept = True,
        ),
        
        # The remove digit function
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(output {1}<$({number})%_> directy if there is only one digit, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)",
            type="::({})",
            axis_name="remove",
            context="the number with the current digit removed",
            description="Remove the rightmost digit from a number",
            reference_data='::(output {1}<$({number})%_> directy if there is only one digit, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)',
            reference_axis_names=["remove"],
            # is_ground_concept = True,
            is_invariant=True
        ),
        
        # The quantifier function
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every({number})%:[{number}]@[{index}^1]",
            type="*every",
            description="Quantifier that processes each digit of the number",
        ),
        
        # The add function for new number
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$+({new number}:{number})",
            type="$+",
            description="Add the new number to the collection",
            is_ground_concept = True,
        ),

        # The dollar function for collection
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.([{index} and {digit}]*)",
            type="$.",
            description="Collect the index-digit pairs",
            is_ground_concept = True,
        ),
        
        # The timing concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@after([{index} and {digit}]*)",
            type="@after",
            description="Execute after the index-digit pair is processed",
            is_ground_concept = True,
        ),
        
        # The in relation for grouping
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="&in({index}*;{digit}*)",
            type="&in",
            description="Group index and digit together",
            is_ground_concept = True,
        ),
        
    ]
    
    # Create concept repository
    concept_repo = ConceptRepo(concept_entries)
    # --- End of initial references ---

    inference_entries = [

        # Quantifying Inference (Syntactic)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('[all {index} and {digit} of number]'),
            function_concept=concept_repo.get_concept('*every({number})%:[{number}]@[{index}^1]'),
            value_concepts=[concept_repo.get_concept('{number}')],
            context_concepts=[concept_repo.get_concept('{index}*'), concept_repo.get_concept('[{index} and {digit}]*'), concept_repo.get_concept('{number}*')],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "syntax": {
                    "marker": "every", 
                    "LoopBaseConcept": "{number}",
                    "InLoopConcept": {
                        "{index}*": 1,
                    },
                    "ConceptToInfer": ["[all {index} and {digit} of number]"],
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_with_support_reference_only=True
        ),

        # --- Inferences inside the loop ---
        # Assigning Inference (Syntactic)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('*every({number})%:[{number}]@[{index}^1]'),
            function_concept=concept_repo.get_concept('$.([{index} and {digit}]*)'),
            value_concepts=[concept_repo.get_concept('[{index} and {digit}]*'), concept_repo.get_concept('{number}'), concept_repo.get_concept('{index}*')],
            flow_info={'flow_index': '1.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "[{index} and {digit}]*",
                    "assign_destination": "*every({number})%:[{number}]@[{index}^1]"
                }
            },
        ),

        # Grouping Inference (Syntactic)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=concept_repo.get_concept('[{index} and {digit}]*'),
            function_concept=concept_repo.get_concept('&in({index}*;{digit}*)'),
            value_concepts=[concept_repo.get_concept('{index}*'), concept_repo.get_concept('{digit}*')],
            context_concepts=[concept_repo.get_concept('{index}*'), concept_repo.get_concept('{digit}*')],
            flow_info={'flow_index': '1.1.2'},
            working_interpretation={
                "syntax": {
                    "marker": "in",
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{digit}*'),
            function_concept=concept_repo.get_concept('::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)'),
            value_concepts=[concept_repo.get_concept('{number}*'), concept_repo.get_concept('{unit place digit}?')],
            flow_info={'flow_index': '1.1.2.3'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{number}*": 1,
                    "{unit place digit}?": 2,
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{number}'),
            function_concept=concept_repo.get_concept('$+({new number}:{number})'),
            value_concepts=[concept_repo.get_concept('{new number}'), concept_repo.get_concept('{number}')],
            flow_info={'flow_index': '1.1.3'},
            working_interpretation={
                "syntax": {
                    "marker": "+",
                    "assign_source": "{new number}",
                    "assign_destination": "{number}"
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{new number}'),
            function_concept=concept_repo.get_concept('::(output {1}<$({number})%_> directy if there is only one digit, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)'),
            value_concepts=[concept_repo.get_concept('{unit place digit}?'), concept_repo.get_concept('{number}*')],
            flow_info={'flow_index': '1.1.3.2'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{number}*": 1,
                    "{unit place digit}?": 2,
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('::(output {1}<$({number})%_> directy if there is only one digit, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)'),
            function_concept=concept_repo.get_concept('@after([{index} and {digit}]*)'),
            value_concepts=[concept_repo.get_concept('@after([{index} and {digit}]*)')],
            flow_info={'flow_index': '1.1.3.2.1'},
            working_interpretation={
                'syntax': {
                    'marker': 'after',
                    'condition': '[{index} and {digit}]*'
                }
            },
            start_without_value=True,
            start_without_function=True
        ),
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{index}*'),
            function_concept=concept_repo.get_concept('::(increase {1}?<$({index})%_>) by one'),
            value_concepts=[concept_repo.get_concept('{index}*')],
            flow_info={'flow_index': '1.1.4'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{index}*": 1,
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('::(increase {1}?<$({index})%_>) by one'),
            function_concept=concept_repo.get_concept('@after([{index} and {digit}]*)'),
            value_concepts=[concept_repo.get_concept('@after([{index} and {digit}]*)')],
            flow_info={'flow_index': '1.1.4.1'},
            working_interpretation={
                'syntax': {
                    'marker': 'after',
                    'condition': '[{index} and {digit}]*'
                }
            },
            start_without_value=True,
            start_without_function=True
        ),

    ]
    
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo

def log_concept_references(concept_repo, concept_name=None):
    """Helper function to log concept references for debugging purposes.
    
    Args:
        concept_repo: The concept repository to inspect
        concept_name: Optional specific concept name to check. If None, logs all concepts.
    """
    if concept_name:
        # Log specific concept reference
        concept = concept_repo.get_concept(concept_name)
        if concept:
            logging.info(f"Concept found: {concept.concept_name}")
            if concept.concept.reference:
                logging.info(f"  - Reference axes: {concept.concept.reference.axes}")
                logging.info(f"  - Reference shape: {concept.concept.reference.shape}")
                logging.info(f"  - Reference tensor: {concept.concept.reference.tensor}")
            else:
                logging.warning("  - No reference found for concept")
        else:
            logging.error(f"Concept '{concept_name}' not found in repository")
    else:
        # Log all concepts in repository
        logging.info("--- All Concepts in Repository ---")
        for concept in concept_repo.get_all_concepts():
            logging.info(f"  - {concept.concept_name}: {concept.type}")
            if concept.concept.reference:
                logging.info(f"    Reference axes: {concept.concept.reference.axes}")
                logging.info(f"    Reference tensor: {concept.concept.reference.tensor}")
            else:
                logging.info(f"    No reference")

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


def validate_digit_counting_output(input_number: str, output_tensor: Any) -> bool:
    """
    Validates that the output from the quantification sequence correctly deconstructed the number.
    Provides detailed logging on missing, incorrect, and correct digits.
    This version is adapted to handle a complex, nested list/dict tensor structure.
    """
    logging.info("\n--- Detailed Validation ---")
    
    reported_digits_map = {}

    def _get_scalar_value(data: Any) -> Optional[str]:
        """Drills down into nested lists to find a single string value."""
        val = data
        while isinstance(val, list):
            if not val: return None
            val = val[0]
        if isinstance(val, str):
            return val.strip('%()')
        return str(val) if val is not None else None

    def _parse_recursive(data: Any):
        """Recursively traverses the output tensor to find and parse digit/index pairs."""
        if isinstance(data, list):
            for item in data:
                _parse_recursive(item)
        elif isinstance(data, dict):
            if '{index}*' in data and '{digit}*' in data:
                index_val = _get_scalar_value(data.get('{index}*'))
                digit_val = _get_scalar_value(data.get('{digit}*'))
                
                if index_val and digit_val and index_val.isdigit() and digit_val.isdigit():
                    reported_digits_map[int(index_val)] = digit_val
            else:
                # Also check dict values for further nested data
                for val in data.values():
                    _parse_recursive(val)

    try:
        _parse_recursive(output_tensor)
        logging.info(f"📊 Parsed {len(reported_digits_map)} unique digits from agent output.")

        # Create the expected map from the input number
        reversed_input = input_number[::-1]
        expected_digits_map = {i + 1: digit for i, digit in enumerate(reversed_input)}
        
        # --- Detailed Comparison ---
        correct_count = 0
        incorrect_digits = []
        missing_digits = []

        expected_indices = set(expected_digits_map.keys())
        reported_indices = set(reported_digits_map.keys())

        # 1. Find missing digits
        missing_indices = expected_indices - reported_indices
        if missing_indices:
            for index in sorted(list(missing_indices)):
                missing_digits.append(f"Index {index} (expected digit '{expected_digits_map[index]}')")

        # 2. Compare reported digits
        for index, reported_digit in reported_digits_map.items():
            if index in expected_digits_map:
                expected_digit = expected_digits_map[index]
                if reported_digit == expected_digit:
                    correct_count += 1
                else:
                    incorrect_digits.append(f"Index {index} (reported '{reported_digit}', expected '{expected_digit}')")

        # --- Logging Summary ---
        logging.info("--- Validation Summary ---")
        logging.info(f"Total digits expected: {len(expected_digits_map)}")
        logging.info(f"Total digits reported by agent: {len(reported_digits_map)}")
        logging.info(f"✅ Correctly identified digits: {correct_count}")

        if incorrect_digits:
            logging.warning(f"⚠️ Incorrectly identified digits: {len(incorrect_digits)}")
            for item in incorrect_digits:
                logging.warning(f"  - {item}")
        
        if missing_digits:
            logging.warning(f"⚠️ Missing digits: {len(missing_digits)}")
            for item in missing_digits:
                logging.warning(f"  - {item}")

        # Final verdict
        is_pass = (len(missing_digits) == 0 and len(incorrect_digits) == 0)
        
        if is_pass and reported_digits_map: # Check if not empty
            sorted_reported = [reported_digits_map[i] for i in sorted(reported_digits_map.keys())]
            reconstructed_reversed = "".join(sorted_reported)
            reconstructed_val = int(reconstructed_reversed[::-1])
            expected_val = int(input_number)
            if reconstructed_val != expected_val:
                logging.error("❌ Validation Failed: Final integer value mismatch. This may indicate extra non-zero digits.")
                is_pass = False

        if is_pass:
            logging.info("✅ Validation Passed!")
        else:
            logging.error("❌ Validation Failed.")
            
        return is_pass

    except Exception as e:
        logging.error(f"❌ An unexpected error occurred during validation: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Setup file logging with timestamp in logs directory
    log_filename = setup_orchestrator_logging(__file__)
    
    # --- Main Execution Logic ---
    logging.info("=== Starting Orchestrator Demo ===")

    # --- Data Definitions ---
    length = 100
    number = generate_random_number(length)
    logging.info(f"Input number: {number}")
    logging.info(f"Input number length: {length}")

    # --- End of Data Definitions ---

    # 1. Create repositories 
    concept_repo, inference_repo = create_sequential_repositories(number)

    # 2. Log the remove concept reference before execution
    log_concept_references(concept_repo, "::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)")
    
    # # 3. Log all concepts in repository for debugging
    # log_concept_references(concept_repo)
    
    # 4. Initialize and run the orchestrator with optional Blackboard and AgentFrameModel
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo, 
        max_cycles=10*length,
    )

    # 3. Run the orchestrator
    final_concepts = orchestrator.run()
    
    logging.info("--- Final Concepts Returned ---")
    final_concept_entry = next((c for c in final_concepts if c.is_final_concept), None)

    if final_concept_entry:
        ref = final_concept_entry.concept.reference
        ref_tensor = ref.tensor if ref is not None else "N/A"
        logging.info(f"  - Final Concept '{final_concept_entry.concept_name}': {ref_tensor}")
        
        if ref is not None:
            validation_result = validate_digit_counting_output(number, ref_tensor)
            print(f"\nInput number was: {number}")
            print(f"Validation Result: {'✅ PASSED' if validation_result else '❌ FAILED'}")
        else:
            print("💥 Validation failed! No reference found in the final concept.")

    else:
        logging.info("  No final concepts were returned.")
        print("💥 Validation failed! No final concept was returned by the orchestrator.")

    logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===") 