import uuid
import logging
import os
import sys

# --- Infra Imports ---
try:
    from infra import Inference, Concept, AgentFrame, Reference, BaseStates
    from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
    from infra._orchest._orchestrator import Orchestrator
    from infra._loggers.utils import setup_orchestrator_logging
    from infra._agent._body import Body
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))
    from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Body
    from infra._loggers.utils import setup_orchestrator_logging


def create_imperative_orchestrator_repos():
    """Creates concept and inference repositories for an imperative_python orchestrator scenario."""
    
    script_name = "add_for_orchest.py"
    script_dir = "generated_scripts"
    script_path = os.path.join(script_dir, script_name)

    # 1. --- Create concept entries ---
    concept_entries = [
        ConceptEntry(id=str(uuid.uuid4()), concept_name='input_1', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='input_2', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='nominalized_action', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='run_python_script_function', type='::({})', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='output_result', type='{}', is_final_concept=True),
    ]
    concept_repo = ConceptRepo(concept_entries)
    
    # 2. --- Add initial references for ground concepts ---
    logging.info("Assigning initial references to ground concepts.")
    concept_repo.add_reference('input_1', ['%(20)'])
    concept_repo.add_reference('input_2', ['%(22)'])
    concept_repo.add_reference('nominalized_action', [f"%{{script_location}}({script_path})"])
    concept_repo.add_reference('run_python_script_function', ['dummy'])

    # 3. --- Define the Inference ---
    inf_to_infer = concept_repo.get_concept('output_result')
    inf_function = concept_repo.get_concept('run_python_script_function')
    inf_values = [
        concept_repo.get_concept('input_1'),
        concept_repo.get_concept('input_2'),
        concept_repo.get_concept('nominalized_action')
    ]

    inference_entries = [
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_python',
            concept_to_infer=inf_to_infer,
            function_concept=inf_function,
            value_concepts=inf_values,
            flow_info={'flow_index': '1'},
            working_interpretation={
                "value_order": {
                    "input_1": 0,
                    "input_2": 1,
                    "nominalized_action": 2
                }
            },
        ),
    ]
    
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo

if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Imperative Python Orchestrator Demo ===")

    # Ensure helper directories exist
    os.makedirs("generated_scripts", exist_ok=True)
    
    # 1. Create repositories 
    concept_repo, inference_repo = create_imperative_orchestrator_repos()

    # 2. Initialize Body with base_dir for relative path resolution
    current_dir = os.path.dirname(__file__)
    body = Body(base_dir=current_dir)

    # 3. Initialize and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body
    )
    final_concepts = orchestrator.run()
    
    # 4. Log the final results
    logging.info("--- Final Concepts Returned ---")
    if final_concepts:
        for concept in final_concepts:
            ref_tensor = concept.concept.reference.tensor if concept.concept and concept.concept.reference is not None else "N/A"
            logging.info(f"  - {concept.concept_name}: {ref_tensor}")
    else:
        logging.info("  No final concepts were returned.")

    logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===")
