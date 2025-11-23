import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

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
    with open(SCRIPT_DIR / '5.1_concept_repo_sim.json', 'r') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)

    with open(SCRIPT_DIR / '5.1_inference_repo_sim.json', 'r') as f:
        inference_data = json.load(f)
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    
    return concept_repo, inference_repo

if __name__ == "__main__":
    # 1. Prepare file system
    (SCRIPT_DIR / "outputs").mkdir(exist_ok=True)

    # 2. Setup logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Simplified Pipeline Execution ===")

    # 3. Build repositories from the generated JSON files
    concept_repo, inference_repo = create_repositories_from_files()

    # 4. Construct a Body for imperatives/judgements
    # Assuming 'qwen-plus' is a valid LLM name in the user's environment.
    body = Body(llm_name="qwen-turbo-latest", base_dir=SCRIPT_DIR)

    # 5. Construct and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body,
        max_cycles=300,
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
