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
    # The script is in infra/examples/or_imperative_python, so we go up 3 levels
    project_root = here.parent.parent.parent 
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Body
    from infra._loggers.utils import setup_orchestrator_logging


def create_imperative_orchestrator_repos():
    """Creates concept and inference repositories for an imperative_python orchestrator scenario."""
    
    script_name = "add_and_structure_for_orchest.py"
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
    # input_1 is a list of values (a relation)
    concept_repo.add_reference('input_1', [['%(20)', '%(30)', '%(40)']], axis_names=['input_1_items'])
    # input_2 is a list of dictionaries
    concept_repo.add_reference('input_2', [[{'value': '%(10)', 'name':'%(number_1)'}, {'value': '%(22)', 'name':'%(number_2)'}]], axis_names=['items'])
    concept_repo.add_reference('nominalized_action', [f"%{{script_location}}({script_path})"], axis_names=['nominalized_action'])
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
                },
                "value_selectors": {
                    "input_1": {
                        "source_concept": "input_1",
                        "index": 0
                    },
                    "input_2": {
                        "source_concept": "input_2",
                        "index": 0,
                        "key": "value"
                    }
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

    # The 'add_for_orchest.py' script is expected to exist in a sibling directory.
    
    # 1. Create repositories 
    concept_repo, inference_repo = create_imperative_orchestrator_repos()

    # 2. Initialize Body with base_dir pointing to the 'examples' directory
    # so that 'generated_scripts/add_for_orchest.py' can be found.
    examples_dir = os.path.dirname(os.path.dirname(__file__))
    body = Body(base_dir=examples_dir)

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
