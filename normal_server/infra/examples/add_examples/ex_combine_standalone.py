import uuid
import logging
import os
import sys
import re
import json

# --- Infra Imports ---

# Ensure project root is in path for imports
import pathlib
here = pathlib.Path(__file__).resolve().parent
# Go up 3 levels: add_examples -> examples -> infra -> project_root
project_root = here.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Blackboard, Reference
from infra._orchest._db import OrchestratorDB
from infra._orchest._checkpoint import CheckpointManager
from infra._loggers.utils import setup_orchestrator_logging
from infra._agent._body import Body


def create_standalone_combine_repository():
    """
    Creates a STANDALONE repository with ONLY the two inferences needed for combining.
    This is NOT an extension - it's a completely independent repository.
    Loads concepts and inferences from JSON files in the repo/ directory.
    
    The infrastructure's checkpoint reconciliation will handle transferring data
    from checkpoints when resuming (via PATCH/OVERWRITE/FILL_GAPS modes).
    """
    logging.info("Creating STANDALONE combine repository from JSON files...")
    
    # Load from JSON files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.join(base_dir, "repo")
    concepts_json = os.path.join(repo_dir, "combination_concepts.json")
    inferences_json = os.path.join(repo_dir, "combination_inferences.json")
    
    # Verify files exist
    if not os.path.exists(concepts_json):
        raise FileNotFoundError(f"Concepts file not found: {concepts_json}")
    if not os.path.exists(inferences_json):
        raise FileNotFoundError(f"Inferences file not found: {inferences_json}")
    
    # Load concepts using ConceptRepo.from_json_list
    with open(concepts_json, 'r', encoding='utf-8') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)
    logging.info(f"  - Loaded {len(concept_repo._concept_map)} concepts from {concepts_json}")
    
    # Load inferences using InferenceRepo.from_json_list
    with open(inferences_json, 'r', encoding='utf-8') as f:
        inference_data = json.load(f)
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    
    logging.info(f"  - Loaded {len(inference_repo.inferences)} inferences from {inferences_json}")
    for inf in inference_repo.inferences:
        logging.info(f"    * Inference (flow {inf.flow_info.get('flow_index')}): {inf.inference_sequence} -> {inf.concept_to_infer.concept_name}")
    
    logging.info("Repository creation completed successfully.")
    return concept_repo, inference_repo

def main():
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the combination orchestrator (combines digits from number pairs)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from a checkpoint (loads {new number pair} from addition checkpoint)')
    parser.add_argument('--db-path', type=str, default="orchestration_checkpoint.db",
                       help='Path to the checkpoint database file (default: orchestration_checkpoint.db)')
    parser.add_argument('--run-id', type=str, default=None,
                       help='Run ID of the addition checkpoint to load from (default: latest run)')
    parser.add_argument('--new-run-id', type=str, default=None,
                       help='New Run ID to fork into (default: uses script default "standalone-combine-test")')
    parser.add_argument('--cycle', type=int, default=None,
                       help='Specific cycle number to load checkpoint from (default: latest)')
    parser.add_argument('--inference-count', type=int, default=None,
                       help='Specific inference count within cycle to load checkpoint from (default: latest)')
    parser.add_argument('--mode', type=str, default="PATCH", choices=["PATCH", "OVERWRITE", "FILL_GAPS"],
                       help='Reconciliation mode: PATCH (smart merge - compares signatures, overwrites if match), OVERWRITE (trust checkpoint completely), FILL_GAPS (only fill empty concepts) (default: PATCH)')
    parser.add_argument('--max-cycles', type=int, default=10,
                       help='Maximum number of cycles to run (default: 10)')
    parser.add_argument('--list-runs', action='store_true',
                       help='List all available runs in the database and exit')
    parser.add_argument('--list-checkpoints', action='store_true',
                       help='List all available checkpoints for the specified run and exit')
    
    args = parser.parse_args()
    
    # Setup
    run_id = "standalone-combine-test"
    setup_orchestrator_logging(__file__, run_id=run_id)
    logging.info("=== Starting Standalone Combine Demo ===")
    
    # Ensure DB path is absolute or relative to script dir
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, args.db_path)
    
    # Handle list commands
    if args.list_runs:
        print("\n" + "="*80)
        print("AVAILABLE RUNS")
        print("="*80)
        try:
            # Use the globally imported OrchestratorDB
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
            checkpoints = Orchestrator.list_available_checkpoints(db_path, run_id=args.run_id)
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
                if args.run_id:
                    print(f"(for run_id: {args.run_id})")
        except Exception as e:
            print(f"Error listing checkpoints: {e}")
        sys.exit(0)
    
    # 1. Create the standalone repository
    # The infrastructure's reconciliation will handle data transfer from checkpoint
    concept_repo, inference_repo = create_standalone_combine_repository()
    
    # 2. Initialize Body
    examples_dir = os.path.dirname(__file__)
    body = Body(llm_name="qwen-plus", base_dir=examples_dir)
    
    # 3. Initialize Orchestrator (either fresh or from checkpoint)
    if args.resume:
        logging.info(f"Resuming from checkpoint: {db_path}")
        logging.info(f"  Run ID: {args.run_id or 'latest'}")
        logging.info(f"  Mode: {args.mode}")
        
        if not os.path.exists(db_path):
            logging.error(f"Checkpoint database not found: {db_path}")
            logging.error("Please run the addition example first to create a checkpoint.")
            sys.exit(1)
        
        orchestrator = Orchestrator.load_checkpoint(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            db_path=db_path,
            body=body,
            max_cycles=args.max_cycles,
            run_id=args.run_id,
            new_run_id=args.new_run_id or run_id,
            cycle=args.cycle,
            inference_count=args.inference_count,
            mode=args.mode,
            validate_compatibility=True
        )
        
        # Check if {new number pair} was loaded from checkpoint
        # The infrastructure's reconciliation (PATCH/OVERWRITE/FILL_GAPS) handles this automatically
        new_number_pair = concept_repo.get_concept('{new number pair}')
        if new_number_pair and new_number_pair.concept and new_number_pair.concept.reference:
            # Check if this came from checkpoint or JSON by checking blackboard status
            # If it was in checkpoint and signatures matched, reconciliation applied it
            status = orchestrator.blackboard.get_concept_status('{new number pair}')
            if status == 'complete':
                logging.info(f"✓ {{new number pair}} is available (from checkpoint or JSON)")
                logging.info(f"  Data shape: {new_number_pair.concept.reference.shape}")
                logging.info(f"  Data axes: {new_number_pair.concept.reference.axes}")
        else:
            logging.warning("⚠ {new number pair} not found or has no reference")
            logging.warning("  Check reconciliation logs above to see if checkpoint data was applied")
    else:
        logging.info("Starting fresh execution (no checkpoint)")
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            run_id=run_id,
            body=body,
            max_cycles=args.max_cycles,
            db_path=db_path  # Ensure checkpointing is enabled!
        )
    
    # 4. Run
    logging.info("Starting execution...")
    final_concepts = orchestrator.run()

    # --- Manual DB Check Start ---
    try:
        print("\n" + "="*60)
        print("--- Manual DB Check for Verification (Post-Run) ---")
        check_db = OrchestratorDB(db_path)
        
        # Check source run (args.run_id)
        if args.run_id:
            print(f"Checking Source Run ID: {args.run_id}")
            src_chk_tuple = check_db.load_latest_checkpoint(run_id=args.run_id)
            if src_chk_tuple:
                cycle, inf_count, chk_data = src_chk_tuple
                print(f"Loaded latest checkpoint for source: Cycle {cycle}, Inference {inf_count}")
                comp_concepts = chk_data.get('completed_concepts', {})
                if '{new number pair}' in comp_concepts:
                    cc_data = comp_concepts['{new number pair}']
                    ref_shape = "Unknown"
                    if 'reference_data' in cc_data:
                        ref_data = cc_data['reference_data']
                        ref_shape = f"Data len: {len(ref_data)}" if isinstance(ref_data, list) else "Data present"
                    print(f"CHECK SOURCE: '{{new number pair}}' is present. {ref_shape}")
                else:
                    print(f"CHECK SOURCE: '{{new number pair}}' NOT found in latest checkpoint.")
                    # List keys to see what's there
                    print(f"Keys in completed_concepts: {list(comp_concepts.keys())}")
            else:
                print(f"CHECK SOURCE: Could not load checkpoint for {args.run_id}")
            print("-" * 40)

        # We want to check the run we just executed
        check_run_id = orchestrator.run_id
        print(f"Checking Run ID: {check_run_id}")

        # Check latest checkpoint for this run
        chk_tuple = check_db.load_latest_checkpoint(run_id=check_run_id)
        
        if chk_tuple:
            cycle, inf_count, chk_data = chk_tuple
            print(f"Loaded latest checkpoint: Cycle {cycle}, Inference {inf_count}")
            
            comp_concepts = chk_data.get('completed_concepts', {})
            
            # Check for {new number pair} (should be preserved if resumed)
            if '{new number pair}' in comp_concepts:
                cc_data = comp_concepts['{new number pair}']
                ref_shape = "Unknown"
                if 'reference_data' in cc_data:
                        ref_data = cc_data['reference_data']
                        ref_shape = f"Data len: {len(ref_data)}" if isinstance(ref_data, list) else "Data present"
                print(f"CHECK: '{{new number pair}}' is present. {ref_shape}")
            else:
                print(f"CHECK: '{{new number pair}}' NOT found in latest checkpoint.")

            # Check for {sum} (newly calculated)
            if '{sum}' in comp_concepts:
                cc_data = comp_concepts['{sum}']
                ref_data = cc_data.get('reference_data')
                print(f"CHECK: '{{sum}}' is present. Value: {ref_data}")
            else:
                print(f"CHECK: '{{sum}}' NOT found in latest checkpoint.")
                
        else:
            print(f"MANUAL CHECK: Could not load 'latest' checkpoint for run '{check_run_id}'")
            # Debug: List all checkpoints to see if any exist
            all_cps = check_db.list_checkpoints(run_id=check_run_id)
            print(f"DEBUG: Found {len(all_cps)} total checkpoints for this run.")
            if all_cps:
                print(f"DEBUG: Last 3 checkpoints: {all_cps[-3:]}")
        print("="*60 + "\n")

    except Exception as e:
        print(f"Manual DB check failed with error: {e}")
    # --- Manual DB Check End ---
    
    # 5. Report
    print("\n" + "="*60)
    print("EXECUTION REPORT")
    print("="*60)
    
    sum_concept = concept_repo.get_concept('{sum}')
    if sum_concept and sum_concept.concept and sum_concept.concept.reference:
        print(f"\nSUCCESS: Final Sum Calculated: {sum_concept.concept.reference.tensor}")
    else:
        print("\nFAILURE: Final Sum not calculated.")
    
    # Show final concepts
    for fc in final_concepts:
        if fc and fc.concept and fc.concept.reference:
            print(f"Final Concept '{fc.concept_name}': {fc.concept.reference.tensor}")

if __name__ == "__main__":
    main()
