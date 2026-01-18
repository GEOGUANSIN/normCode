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
# Ensure project root is in path for imports
import pathlib
here = pathlib.Path(__file__).resolve().parent
# Go up 3 levels: add_examples -> examples -> infra -> project_root
project_root = here.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infra import Inference, Concept, AgentFrame, Reference, BaseStates
from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Blackboard, Body
from infra._orchest._blackboard import Blackboard
from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
from infra._orchest._waitlist import WaitlistItem, Waitlist
from infra._orchest._tracker import ProcessTracker
from infra._orchest._orchestrator import Orchestrator
from infra._orchest._db import OrchestratorDB
from infra._orchest._checkpoint import CheckpointManager
from infra._loggers.utils import setup_orchestrator_logging
from infra._agent._body import Body

# Import the result validator and random number generator
from result_validator import ResultValidator
from random_number_generator import RandomNumberGenerator, quick_generate, generate_test_suite



# --- Normcode for this example ---

Normcode_new_with_appending = """
{new number pair} | 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>] | 1.1. assigning

        <= $.({remainder}) 
        
        <- {digit sum} | 1.1.2. imperative
            <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
            <- {sum}?<:{3}>
            <- {carry-over number}*1<:{2}> 
            <- [all {unit place value} of numbers]<:{1}> | 1.1.2.4. grouping
                <= &across({unit place value}:{number pair}*1)
                <- {unit place value} | 1.1.2.4.2. quantifying
                    <= *every({number pair}*1)%:[{number}]@(2) | 1.1.2.4.2.1. assigning
                        <= $.({single unit place value})
                        <- {single unit place value} | 1.1.2.4.2.1.2. imperative
                            <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)
                            <- {unit place digit}?<:{2}>
                            <- {number pair}*1*2
                    <- {number pair}*1

        <- {number pair}<$={1}> | 1.1.3. assigning
            <= $+({number pair to append}:{number pair})%:[{number pair}] | 1.1.3.1. timing
                <= @if!(<all number is 0>) | 1.1.3.1.1. timing
                    <= @if(<carry-over number is 0>)

            <- {number pair to append}<$={1}> | 1.1.3.2. quantifying
                <= *every({number pair}*1)%:[{number}]@(3) | 1.1.3.2.1. assigning
                    <= $.({number with last digit removed}) 
                    <- {number with last digit removed} | 1.1.3.2.1.2. imperative
                        <= ::(output 0 if {1}<$({number})%_> is less than 10, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>) 
                        <- {unit place digit}?<:{2}> 
                        <- {number pair}*1*3<:{1}>
                <- {number pair}*1

            <- <all number is 0> | 1.1.3.3. judgement
                <= :%(True):<{1}<$({number})%_> is 0> | 1.1.3.3.1. timing
                    <= @after({number pair to append}<$={1}>)
                <- {number pair to append}<$={1}><:{1}>

            <- <carry-over number is 0> | 1.1.3.4. judgement
                <= :%(True):<{1}<$({carry-over number})%_> is 0> | 1.1.3.4.1. timing
                    <= @after({number pair to append}<$={1}>)
                <- {carry-over number}*1 | 1.1.3.4.2. grouping
                    <= &across({carry-over number}*1:{carry-over number}*1<--<!_>>)
                    <- {carry-over number}*1 | 1.1.3.4.2.2. imperative
                        <= ::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10) | 1.1.3.4.2.2.1. timing
                            <= @after({digit sum})
                        <- {quotient}?<:{1}>
                        <- {digit sum}<:{2}>

        <- {remainder} | 1.1.4. imperative
            <= ::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10) | 1.1.4.1. timing
                <= @after({digit sum})
            <- {remainder}?<:{1}>
            <- {digit sum}<:{2}>

    <- {number pair}<$={1}> |ref. %(number pair)=[%(number)=[123, 98]]
"""


Normcode_combine = """
{sum} | 1. imperative
    <- ::(comebine all {1}<$({number digits})%_>)
    <- {new number pair} | 1.1. grouping
        <= &across({new number pair}:{new number pair}<--<!_>>)
        <- {new number pair}
"""


# --- Data Definitions ---

def create_appending_repositories(number_1: str = "123", number_2: str = "98", imperative_seqeunce: str = "imperative_python_indirect", judgement_seqeunce: str = "judgement_python_indirect"):
    """
    Creates concept and inference repositories for the appending scenario.
    Loads concepts and inferences entirely from JSON files, similar to ex_combine_standalone.py.
    Only adds the dynamic {number pair} reference based on input parameters.
    """
    import json
    
    # Load from JSON files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.join(base_dir, "repo")
    concepts_json = os.path.join(repo_dir, "addition_concepts.json")
    inferences_json = os.path.join(repo_dir, "addition_inferences.json")
    
    # Verify files exist
    if not os.path.exists(concepts_json):
        raise FileNotFoundError(f"Concepts file not found: {concepts_json}")
    if not os.path.exists(inferences_json):
        raise FileNotFoundError(f"Inferences file not found: {inferences_json}")
    
    logging.info(f"Loading concepts from: {concepts_json}")
    with open(concepts_json, 'r', encoding='utf-8') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)
    logging.info(f"  - Loaded {len(concept_repo._concept_map)} concepts from JSON")
    
    # Add dynamic reference for {number pair} based on input parameters
    # This is the only programmatic addition - all other concepts and references are in JSON
    concept_repo.add_reference(
        '{number pair}',
        [["%(" + number_1 + ")", "%(" + number_2 + ")"]],
        axis_names=["number pair", "number"]
    )
    
    # Load inferences from JSON
    logging.info(f"Loading inferences from: {inferences_json}")
    with open(inferences_json, 'r', encoding='utf-8') as f:
        inference_data = json.load(f)
    
    # Update inference_sequence in JSON data if needed (for dynamic sequence names)
    for inf_item in inference_data:
        if inf_item.get('inference_sequence') == 'imperative_python_indirect':
            inf_item['inference_sequence'] = imperative_seqeunce
        elif inf_item.get('inference_sequence') == 'judgement_python_indirect':
            inf_item['inference_sequence'] = judgement_seqeunce
    
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    logging.info(f"  - Loaded {len(inference_repo.inferences)} inferences from JSON")
    
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
    
    # Find the {new number pair} concept
    new_number_pair_concept = None
    for concept_entry in final_concepts:
        if concept_entry and concept_entry.concept_name == '{new number pair}':
            new_number_pair_concept = concept_entry
            break
    
    if not new_number_pair_concept:
        logging.error("Could not find '{new number pair}' concept in final results")
        return None
    
    if not new_number_pair_concept.concept.reference:
        logging.error("No reference found for '{new number pair}' concept")
        return None
    
    # Extract the data
    ref = new_number_pair_concept.concept.reference
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
        concept_name='{new number pair}',
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
            concept_repo, inference_repo = create_appending_repositories(
                number_1=number_1,
                number_2=number_2
            )
            
            # Initialize and run the orchestrator
            orchestrator = Orchestrator(
                concept_repo=concept_repo,
                inference_repo=inference_repo,
                max_cycles=18*(len(number_1)+len(number_2)),
                checkpoint_frequency=None  # Random mode doesn't use checkpointing by default
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
    parser = argparse.ArgumentParser(description='Run the number pair addition orchestrator')
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
    parser.add_argument('--number1', type=str, default="12",
                       help='First number for fixed input mode (default: "12")')
    parser.add_argument('--number2', type=str, default="92",
                       help='Second number for fixed input mode (default: "92")')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from the last checkpoint if available (default: auto-resume if checkpoint exists)')
    parser.add_argument('--fresh', action='store_true',
                       help='Force a fresh start, ignoring any existing checkpoint')
    parser.add_argument('--max-cycles', type=int, default=50,
                       help='Maximum number of cycles to run (default: 50). When resuming, this is the total limit.')
    parser.add_argument('--additional-cycles', type=int, default=None,
                       help='Additional cycles to run beyond the checkpoint (overrides --max-cycles when resuming)')
    parser.add_argument('--db-path', type=str, default="orchestration_checkpoint.db",
                       help='Path to the checkpoint database file')
    parser.add_argument('--checkpoint-frequency', type=int, default=2,
                       help='Save checkpoint every N inferences within a cycle (default: 2, set to None to only checkpoint at end of cycle)')
    parser.add_argument('--run-id', type=str, default="demo-run",
                       help='Run ID to use for this execution (default: "demo-run" for easy continuation, set to "None" to generate random ID)')
    parser.add_argument('--cycle', type=int, default=None,
                       help='Specific cycle number to load checkpoint from (default: None, uses latest)')
    parser.add_argument('--inference-count', type=int, default=None,
                       help='Specific inference count within cycle to load checkpoint from (default: None, uses latest for cycle)')
    parser.add_argument('--list-runs', action='store_true',
                       help='List all available runs in the database and exit')
    parser.add_argument('--list-checkpoints', action='store_true',
                       help='List all available checkpoints for the specified run and exit')
    
    args = parser.parse_args()
    
    # Ensure DB path is absolute or relative to script dir
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, args.db_path)

    # Handle list commands
    if args.list_runs:
        print("\n" + "="*80)
        print("AVAILABLE RUNS")
        print("="*80)
        try:
            db = OrchestratorDB(db_path)
            runs = db.list_runs()
            if runs:
                for i, run in enumerate(runs, 1):
                    print(f"\nRun {i}:")
                    print(f"  Run ID: {run['run_id']}")
                    print(f"  First Execution: {run['first_execution']}")
                    print(f"  Last Execution: {run['last_execution']}")
                    print(f"  Execution Count: {run['execution_count']}")
                    print(f"  Max Cycle: {run['max_cycle']}")
            else:
                print("No runs found in database.")
        except Exception as e:
            print(f"Error listing runs: {e}")
        sys.exit(0)
    
    if args.list_checkpoints:
        print("\n" + "="*80)
        print("AVAILABLE CHECKPOINTS")
        print("="*80)
        try:
            run_id_for_list = args.run_id if args.run_id != "None" else None
            checkpoints = Orchestrator.list_available_checkpoints(db_path, run_id=run_id_for_list)
            if checkpoints:
                print(f"\nFound {len(checkpoints)} checkpoint(s):")
                for i, cp in enumerate(checkpoints, 1):
                    print(f"\nCheckpoint {i}:")
                    print(f"  Run ID: {cp['run_id']}")
                    print(f"  Cycle: {cp['cycle']}")
                    print(f"  Inference Count: {cp.get('inference_count', 0)}")
                    print(f"  Timestamp: {cp['timestamp']}")
            else:
                print("No checkpoints found.")
                if run_id_for_list:
                    print(f"(for run_id: {run_id_for_list})")
        except Exception as e:
            print(f"Error listing checkpoints: {e}")
        sys.exit(0)

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
        
        # Determine run_id early so we can use it in logging
        # Use the specified run_id (default is "demo-run" for easy continuation)
        run_id_to_use = args.run_id if args.run_id != "None" else None
        
        # Setup file logging with run_id
        log_filename = setup_orchestrator_logging(__file__, run_id=run_id_to_use)
        logging.info("=== Starting Orchestrator Demo ===")

        # --- Create generated code directories if they don't exist ---
        examples_dir = os.path.dirname(__file__)
        script_dir_gen = os.path.join(examples_dir, "generated_scripts")
        prompt_dir_gen = os.path.join(examples_dir, "generated_prompts")
        os.makedirs(script_dir_gen, exist_ok=True)
        os.makedirs(prompt_dir_gen, exist_ok=True)

        # 1. Create repositories
        length_max = 10
        # If resuming, we might want to use the same numbers as before, but for now 
        # we assume the user provides the same inputs or we just use the defaults/generated ones.
        # Ideally, inputs should be part of the restored state if they are ground concepts.
        # Since ground concepts are part of the repo, and repo is passed to load_checkpoint,
        # we need to make sure we reconstruct the repo correctly.
        
        # For this example, we regenerate/use the numbers. 
        # Note: If resuming, the Orchestrator will reconcile state. 
        # If ground concepts were already complete in the DB, they will remain complete.
        
        number_1, number_2 = quick_generate(min_length=length_max/2, max_length=length_max, seed=25)
        # Override with args if provided (logic could be improved here to respect args always if not generating)
        # logic in original script was generating large numbers. 
        # Let's stick to the generation logic for consistency with "complete_code" example.
        
        logging.info(f"Generated numbers: {number_1} + {number_2}")

        concept_repo, inference_repo = create_appending_repositories(
            number_1=number_1,
            number_2=number_2,
            imperative_seqeunce="imperative_python",
            judgement_seqeunce="judgement_python"
        )

        # Initialize Body
        body = Body(llm_name="qwen-plus", base_dir=examples_dir)

        # 2. Initialize and run the orchestrator
        # Determine if we should resume (default: auto-resume if checkpoint exists, unless --fresh is set)
        should_resume = False
        checkpoint_cycle = 0
        checkpoint_inference_count = 0
        
        if not args.fresh and os.path.exists(db_path):
            # Check if checkpoint exists and get current cycle
            try:
                db = OrchestratorDB(db_path, run_id=run_id_to_use)
                checkpoint_manager = CheckpointManager(db)
                
                # If specific cycle/inference_count provided, use those; otherwise get latest
                if args.cycle is not None:
                    checkpoint_data = checkpoint_manager.load_checkpoint_by_cycle(
                        args.cycle, 
                        run_id=run_id_to_use,
                        inference_count=args.inference_count
                    )
                    if checkpoint_data:
                        checkpoint_cycle = args.cycle
                        checkpoint_inference_count = args.inference_count or 0
                        should_resume = True
                        print(f"--- Found checkpoint at cycle {checkpoint_cycle}, inference {checkpoint_inference_count} ---")
                else:
                    checkpoint_data = checkpoint_manager.load_latest_checkpoint(run_id=run_id_to_use)
                    if checkpoint_data:
                        # Get cycle count from checkpoint (we need to query DB to get the actual cycle/inference)
                        # Since load_latest_checkpoint doesn't return cycle/inference, we'll query the DB
                        checkpoints = db.list_checkpoints(run_id_to_use)
                        if checkpoints:
                            latest = checkpoints[-1]  # Last checkpoint (ordered by cycle ASC, inference_count ASC)
                            checkpoint_cycle = latest['cycle']
                            checkpoint_inference_count = latest.get('inference_count', 0)
                        else:
                            # Fallback: get from tracker in checkpoint data
                            checkpoint_cycle = checkpoint_data.get("tracker", {}).get("cycle_count", 0)
                        should_resume = True
                        print(f"--- Found latest checkpoint at cycle {checkpoint_cycle}, inference {checkpoint_inference_count} ---")
            except Exception as e:
                logging.warning(f"Could not read checkpoint: {e}. Starting fresh.")
                should_resume = False
        
        if should_resume:
            # Calculate max_cycles: use additional_cycles if specified, otherwise add max_cycles to checkpoint
            if args.additional_cycles is not None:
                max_cycles = checkpoint_cycle + args.additional_cycles
                print(f"--- Resuming from cycle {checkpoint_cycle}, inference {checkpoint_inference_count}")
                print(f"    Will run for {args.additional_cycles} additional cycles (total: {max_cycles}) ---")
            else:
                # Default: add max_cycles to the checkpoint cycle (e.g., if at cycle 50 and max_cycles=50, run until 100)
                max_cycles = checkpoint_cycle + args.max_cycles
                print(f"--- Resuming from cycle {checkpoint_cycle}, inference {checkpoint_inference_count}")
                print(f"    Will run for {args.max_cycles} additional cycles (total: {max_cycles}) ---")
            
            logging.info(f"Resuming orchestration from {db_path} (cycle {checkpoint_cycle}, inference {checkpoint_inference_count}, max_cycles={max_cycles})")
            orchestrator = Orchestrator.load_checkpoint(
                concept_repo=concept_repo,
                inference_repo=inference_repo,
                db_path=db_path,
                body=body,
                max_cycles=max_cycles,
                run_id=run_id_to_use,
                cycle=args.cycle if args.cycle is not None else None,
                inference_count=args.inference_count if args.inference_count is not None else None
            )
            
            # Display run_id information
            if orchestrator.run_id:
                print(f"--- Using run_id: {orchestrator.run_id} ---")
        else:
            if args.fresh:
                print("Starting fresh execution (--fresh flag set).")
            elif args.resume:
                print(f"Checkpoint not found at {db_path}. Starting fresh.")
            else:
                print("Starting fresh execution (no checkpoint found).")
            
            # Clean up old DB if starting fresh
            if args.fresh and os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    print(f"Removed old checkpoint DB: {db_path}")
                except Exception as e:
                    print(f"Warning: Could not remove old DB: {e}")

            orchestrator = Orchestrator(
                concept_repo=concept_repo,
                inference_repo=inference_repo,
                body=body,
                # max_cycles=20*length_max,
                max_cycles=args.max_cycles,
                db_path=db_path,
                checkpoint_frequency=args.checkpoint_frequency,
                run_id=run_id_to_use
            )
            
            # Display run_id and checkpoint frequency information
            if orchestrator.run_id:
                print(f"--- New run_id: {orchestrator.run_id} ---")
            if args.checkpoint_frequency:
                print(f"--- Checkpoint frequency: every {args.checkpoint_frequency} inferences ---")

        # 3. Run the orchestrator
        try:
            final_concepts = orchestrator.run()
        except KeyboardInterrupt:
            print("\n\n!!! Execution interrupted by user !!!")
            print("State has been saved to checkpoint.")
            if orchestrator.run_id:
                print(f"Run ID: {orchestrator.run_id}")
            print(f"Run with --resume to continue from the last checkpoint.")
            if orchestrator.run_id:
                print(f"Or specify: --run-id {orchestrator.run_id} --resume")
            sys.exit(0)

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
        
        # Optional: Export full state for debugging
        try:
            full_state = orchestrator.export_state()
            import json
            # Filter out non-serializable parts for a quick dump if needed, or rely on export_state doing it right
            # For now just print confirmation
            print(f"\nFinal State Export contains {len(full_state.get('execution_history', []))} execution records.")
            if orchestrator.run_id:
                print(f"Run ID: {orchestrator.run_id}")
                print(f"To resume this run, use: --run-id {orchestrator.run_id} --resume")
        except Exception as e:
            logging.error(f"Failed to export final state: {e}")
        
        # Display checkpoint information
        if orchestrator.checkpoint_manager:
            try:
                checkpoints = orchestrator.checkpoint_manager.list_checkpoints(orchestrator.run_id)
                if checkpoints:
                    print(f"\n{'='*60}")
                    print(f"CHECKPOINT SUMMARY (Run ID: {orchestrator.run_id})")
                    print(f"{'='*60}")
                    print(f"Total checkpoints: {len(checkpoints)}")
                    if len(checkpoints) <= 10:
                        print("\nCheckpoints:")
                        for cp in checkpoints:
                            print(f"  Cycle {cp['cycle']}, Inference {cp.get('inference_count', 0)}: {cp['timestamp']}")
                    else:
                        print(f"\nFirst 5 checkpoints:")
                        for cp in checkpoints[:5]:
                            print(f"  Cycle {cp['cycle']}, Inference {cp.get('inference_count', 0)}: {cp['timestamp']}")
                        print(f"\n... and {len(checkpoints) - 5} more")
                        print(f"\nLast checkpoint:")
                        last = checkpoints[-1]
                        print(f"  Cycle {last['cycle']}, Inference {last.get('inference_count', 0)}: {last['timestamp']}")
            except Exception as e:
                logging.warning(f"Could not list checkpoints: {e}")
    
    print(f"\n{'='*80}")
    print("PROGRAM COMPLETED")
    print(f"{'='*80}")
