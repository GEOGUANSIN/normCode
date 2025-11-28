import sys
from pathlib import Path
import argparse
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from infra._orchest._repo import ConceptRepo, InferenceRepo
from infra._orchest._orchestrator import Orchestrator
from infra._agent._body import Body
from infra._loggers.utils import setup_orchestrator_logging
import logging
import os
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()

def create_repositories_from_files():
    with open(SCRIPT_DIR / 'repos/5.1_concept_repo_sim.json', 'r') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)

    with open(SCRIPT_DIR / 'repos/5.1_inference_repo_sim.json', 'r') as f:
        inference_data = json.load(f)
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    
    return concept_repo, inference_repo

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run NormCode orchestration with checkpointing support.")
    parser.add_argument("--resume", action="store_true", help="Resume execution from the last checkpoint.")
    args = parser.parse_args()

    # 1. Prepare file system
    (SCRIPT_DIR / "next_iteration").mkdir(exist_ok=True)

    # 2. Setup logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Simplified Pipeline Execution ===")

    # 3. Build repositories from the generated JSON files
    concept_repo, inference_repo = create_repositories_from_files()

    # 4. Construct a Body for imperatives/judgements
    # Assuming 'qwen-plus' is a valid LLM name in the user's environment.
    body = Body(llm_name="qwen-plus", base_dir=SCRIPT_DIR, new_user_input_tool=True)

    # Define database path for checkpointing
    db_path = SCRIPT_DIR / "orchestration.db"
    logging.info(f"Database path: {db_path}")

    # 5. Construct and run the orchestrator
    if args.resume and db_path.exists():
        logging.info(f"--- Resuming from checkpoint: {db_path} ---")
        orchestrator = Orchestrator.load_checkpoint(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            db_path=str(db_path),
            body=body,
            max_cycles=300
        )
    else:
        if args.resume:
            logging.warning("Resume requested but DB not found. Starting fresh.")
        
        # If starting fresh, remove existing DB to ensure a clean state
        if db_path.exists():
            try:
                os.remove(db_path)
                logging.info("Removed existing database for fresh start.")
            except OSError as e:
                logging.warning(f"Could not remove existing DB: {e}")

        logging.info("--- Starting Fresh Execution ---")
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            body=body,
            max_cycles=300,
            db_path=str(db_path)  # Enable checkpointing
        )

    final_concepts = orchestrator.run()

    # 6. Inspect and log final concepts
    logging.info("--- Execution finished. Final concepts: ---")
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            ref_tensor = final_concept_entry.concept.reference.tensor
            logging.info(f"Final concept '{final_concept_entry.concept_name}': {ref_tensor}")
        else:
            logging.info(f"No reference found for final concept '{final_concept_entry.concept_name}'.")
    
    logging.info(f"=== Simplified Execution Complete - Log saved to {log_filename} ===")
