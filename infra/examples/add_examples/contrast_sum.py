import uuid
import logging
import sys
from typing import Optional

# --- Infra Imports ---
try:
    from infra import ConceptRepo, InferenceRepo, Orchestrator
    from infra._orchest._repo import ConceptEntry, InferenceEntry
    from infra._loggers.utils import setup_orchestrator_logging
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent.parent))
    from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator
    from infra._loggers.utils import setup_orchestrator_logging

# Import the result validator and random number generator
from result_validator import ResultValidator
from random_number_generator import RandomNumberGenerator, quick_generate, generate_test_suite


# --- Normcode for this example ---

Normcode_simple_addition = """
{sum} | 1. imperative
    <= ::(sum the {1}<$({number pair})%_> and obtain the {2}?<$({sum})%_>)
    <- {number pair}<:{2}> |ref. %(number pair)=[[123, 98]]
    <- {sum}?<:{1}>
"""

# --- Data Definitions ---

def create_simple_addition_repositories(number_1: str = "123", number_2: str = "98"):
    """Creates concept and inference repositories for the simple addition scenario."""
    # --- Concept Entries ---
    concept_entries = [
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}",
            type="{}",
            axis_name="number pair",
            description="The collection of number pairs.",
            reference_data=[[f"%({number_1})", f"%({number_2})"]],
            reference_axis_names=["number pair"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{sum}",
            type="{}",
            axis_name="sum",
            description="The final sum of the number pair.",
            is_final_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{sum}?",
            type="{}",
            axis_name="sum_query",
            context="query for the sum",
            description="A query for the sum of numbers.",
            reference_data=['the addition result of numbers'],
            reference_axis_names=["sum_query"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(sum the {1}<$({number pair})%_> and obtain the {2}?<$({sum})%_>)",
            type="::({})",
            description="Adds the numbers in a pair.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::(sum the {1}<$({number pair})%_> and obtain the {2}?<$({sum})%_>)"],
            reference_axis_names=["sum_function"],
        ),
    ]
    concept_repo = ConceptRepo(concept_entries)

    # --- Inference Entries ---
    inference_entries = [
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{sum}'),
            function_concept=concept_repo.get_concept('::(sum the {1}<$({number pair})%_> and obtain the {2}?<$({sum})%_>)'),
            value_concepts=[
                concept_repo.get_concept('{number pair}'),
                concept_repo.get_concept('{sum}?'),
            ],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{number pair}": 1,
                    "{sum}?": 2
                },
            },
        ),
    ]
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo


def validate_orchestrator_results(final_concepts, input_numbers):
    """
    Validate the results from the orchestrator using the ResultValidator.
    
    Args:
        final_concepts: List of final concept entries from the orchestrator
        input_numbers: Tuple of input numbers (number_1, number_2)
        
    Returns:
        ValidationResult object with detailed analysis
    """
    validator = ResultValidator()
    
    # Find the {sum} concept
    sum_concept = None
    for concept_entry in final_concepts:
        if concept_entry and concept_entry.concept_name == '{sum}':
            sum_concept = concept_entry
            break
    
    if not sum_concept:
        logging.error("Could not find '{sum}' concept in final results")
        return None
    
    if not sum_concept.concept.reference:
        logging.error("No reference found for '{sum}' concept")
        return None
    
    # Extract the data
    ref = sum_concept.concept.reference
    data_tensor = ref.tensor
    axis_names = ref.axes
    shape = ref.shape
    
    logging.info("=== VALIDATING ORCHESTRATOR RESULTS ===")
    logging.info(f"Input numbers: {input_numbers}")
    logging.info(f"Data tensor: {data_tensor}")
    logging.info(f"Axis names: {axis_names}")
    logging.info(f"Shape: {shape}")
    
    # Perform validation
    validation_result = validator.validate_final_concept(
        concept_name='{sum}',
        data_tensor=data_tensor,
        axis_names=axis_names,
        shape=shape,
        input_numbers=input_numbers
    )
    
    # Print validation report
    validator.print_validation_report(validation_result)
    
    # Log validation results
    logging.info(f"Validation result: {'VALID' if validation_result.is_valid else 'INVALID'}")
    if validation_result.errors:
        for error in validation_result.errors:
            logging.error(f"Validation error: {error}")
    if validation_result.warnings:
        for warning in validation_result.warnings:
            logging.warning(f"Validation warning: {warning}")
    
    return validation_result


def run_with_random_numbers(min_length: int = 1, 
                           max_length: int = 5, 
                           seed: Optional[int] = None,
                           include_edge_cases: bool = True,
                           include_carry_cases: bool = True,
                           test_count: int = 10):
    """
    Run the orchestrator with random number inputs and validate results.
    
    Args:
        min_length: Minimum number of digits (default: 1)
        max_length: Maximum number of digits (default: 5)
        seed: Optional seed for reproducible generation
        include_edge_cases: Whether to include edge cases (default: True)
        include_carry_cases: Whether to include carry cases (default: True)
        test_count: Number of random test cases to generate (default: 10)
    """
    print(f"\n{'='*80}")
    print("RUNNING ORCHESTRATOR WITH RANDOM NUMBER INPUTS")
    print(f"{'='*80}")
    print(f"Configuration:")
    print(f"  - Min/Max length: {min_length}/{max_length}")
    print(f"  - Seed: {seed}")
    print(f"  - Include edge cases: {include_edge_cases}")
    print(f"  - Include carry cases: {include_carry_cases}")
    print(f"  - Test count: {test_count}")
    
    # Generate test cases
    test_cases = generate_test_suite(
        count=test_count,
        include_edge_cases=include_edge_cases,
        include_carry_cases=include_carry_cases,
        min_length=min_length,
        max_length=max_length,
        seed=seed
    )
    
    print(f"\nGenerated {len(test_cases)} test cases")
    
    # Run tests
    results = []
    for i, (number_1, number_2) in enumerate(test_cases):
        print(f"\n{'-'*60}")
        print(f"TEST CASE {i+1}/{len(test_cases)}: {number_1} + {number_2}")
        print(f"{'-'*60}")
        
        try:
            # Create repositories with current numbers
            concept_repo, inference_repo = create_simple_addition_repositories(
                number_1=number_1,
                number_2=number_2
            )
            
            # Initialize and run the orchestrator
            orchestrator = Orchestrator(
                concept_repo=concept_repo,
                inference_repo=inference_repo,
                max_cycles=10,
            )
            
            # Run the orchestrator
            final_concepts = orchestrator.run()
            
            # Validate the results
            validation_result = validate_orchestrator_results(final_concepts, (number_1, number_2))
            
            # Store results
            result_summary = {
                'input': (number_1, number_2),
                'expected_sum': int(number_1) + int(number_2),
                'validation_passed': validation_result.is_valid if validation_result else False,
                'errors': validation_result.errors if validation_result else [],
                'warnings': validation_result.warnings if validation_result else [],
                'accuracy': validation_result.digit_analysis.get('summary', {}).get('accuracy_percentage', 0) if validation_result else 0
            }
            results.append(result_summary)
            
            # Quick status
            status = "✓ PASS" if result_summary['validation_passed'] else "✗ FAIL"
            print(f"\n{status} - Accuracy: {result_summary['accuracy']:.1f}%")
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            result_summary = {
                'input': (number_1, number_2),
                'expected_sum': int(number_1) + int(number_2),
                'validation_passed': False,
                'errors': [f"Execution error: {str(e)}"],
                'warnings': [],
                'accuracy': 0
            }
            results.append(result_summary)
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['validation_passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print(f"\nFailed test cases:")
        for i, result in enumerate(results):
            if not result['validation_passed']:
                input_str = f"{result['input'][0]} + {result['input'][1]}"
                print(f"  {i+1}. {input_str} (Expected: {result['expected_sum']})")
                for error in result['errors']:
                    print(f"     Error: {error}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the simple addition orchestrator')
    parser.add_argument('--random', action='store_true', 
                       help='Run with random number inputs instead of fixed values')
    parser.add_argument('--min-length', type=int, default=1,
                       help='Minimum number of digits for random generation (default: 1)')
    parser.add_argument('--max-length', type=int, default=5,
                       help='Maximum number of digits for random generation (default: 5)')
    parser.add_argument('--test-count', type=int, default=10,
                       help='Number of random test cases to run (default: 10)')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed for reproducible generation (default: None)')
    parser.add_argument('--no-edge-cases', action='store_true',
                       help='Exclude edge cases from random testing')
    parser.add_argument('--no-carry-cases', action='store_true',
                       help='Exclude carry cases from random testing')
    parser.add_argument('--number1', type=str, default="123",
                       help='First number for fixed input mode (default: "123")')
    parser.add_argument('--number2', type=str, default="98",
                       help='Second number for fixed input mode (default: "98")')
    
    args = parser.parse_args()
    
    if args.random:
        # Run with random numbers
        print("Running in RANDOM MODE")
        results = run_with_random_numbers(
            min_length=args.min_length,
            max_length=args.max_length,
            seed=args.seed,
            include_edge_cases=not args.no_edge_cases,
            include_carry_cases=not args.no_carry_cases,
            test_count=args.test_count
        )
    else:
        # Run with fixed numbers (original behavior)
        print("Running in FIXED MODE")
        
        # Setup file logging
        log_filename = setup_orchestrator_logging(__file__)
        logging.info("=== Starting Orchestrator Simple Addition Demo ===")

        # 1. Create repositories
        # number_1 = args.number1
        # number_2 = args.number2
        length_max = 200
        number_1, number_2 = quick_generate(min_length=150, max_length=length_max, seed=25)
        logging.info(f"Input numbers: {number_1} + {number_2}")

        concept_repo, inference_repo = create_simple_addition_repositories(
            number_1=number_1,
            number_2=number_2
        )

        # 2. Initialize and run the orchestrator
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            max_cycles=10,
        )

        # 3. Run the orchestrator
        final_concepts = orchestrator.run()

        # 4. Log the final result
        logging.info("--- Final Concepts Returned ---")
        for final_concept_entry in final_concepts:
            if final_concept_entry and final_concept_entry.concept.reference:
                ref_tensor = final_concept_entry.concept.reference.tensor
                logging.info(f"  - Final Concept '{final_concept_entry.concept_name}': {ref_tensor}")
                print(f"\nFinal concept '{final_concept_entry.concept_name}' tensor: {ref_tensor}")
            else:
                logging.warning(f"No reference found for final concept '{final_concept_entry.concept_name}'.")
                print(f"\nNo reference found for final concept '{final_concept_entry.concept_name}'.")

        # 5. Validate the results
        print("\n" + "="*60)
        print("VALIDATING RESULTS")
        print("="*60)
        validation_result = validate_orchestrator_results(final_concepts, (number_1, number_2))
        
        if validation_result and validation_result.is_valid:
            print("\n🎉 All validations passed!")
        elif validation_result:
            print(f"\n❌ Validation failed with {len(validation_result.errors)} errors")
        else:
            print("\n⚠️  Validation could not be completed")

        logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===")
    
    print(f"\n{'='*80}")
    print("PROGRAM COMPLETED")
    print(f"{'='*80}") 