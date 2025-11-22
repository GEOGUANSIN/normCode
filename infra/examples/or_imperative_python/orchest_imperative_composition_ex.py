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
    # The project root is three levels up from this script's directory
    project_root = here.parent.parent.parent
    sys.path.insert(0, str(project_root))
    from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Body
    from infra._loggers.utils import setup_orchestrator_logging


def create_imperative_composition_repos():
    """Creates concept and inference repositories for an imperative_in_composition orchestrator scenario."""
    
    # --- Define file paths ---
    output_filename = "generated_greeting.txt"
    output_dir = "generated_files"
    save_path = os.path.join(output_dir, output_filename)
    os.makedirs(output_dir, exist_ok=True)

    # 1. --- Create concept entries ---
    concept_entries = [
        ConceptEntry(id=str(uuid.uuid4()), concept_name='input_1', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='input_2', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='prompt_info', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='save_path', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='greeting_function', type='::({})', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='final_greeting', type='{}', is_final_concept=True),
    ]
    concept_repo = ConceptRepo(concept_entries)
    
    # 2. --- Add initial references for ground concepts ---
    logging.info("Assigning initial references to ground concepts.")
    prompt_template_str = (
        "You are a friendly assistant. Your response must be a JSON object "
        "with two keys: 'thinking' (your reasoning) and 'answer' (the final greeting string). "
        "Create a friendly greeting for $input_1 from $input_2."
    )
    
    # The MVP step expects a special string format to identify the prompt template.
    prompt_info_value = f"{{%{{prompt_template}}: {prompt_template_str}}}"
    save_path_value = f"%{{save_path}}id({save_path})"

    concept_repo.add_reference('input_1', [f'%9e3(Alice)'])
    concept_repo.add_reference('input_2', [f'%93t(Wonderland)'])
    concept_repo.add_reference('prompt_info', [prompt_info_value])
    concept_repo.add_reference('save_path', [save_path_value])
    concept_repo.add_reference('greeting_function', ['dummy']) # Functional concept needs a placeholder

    # 3. --- Define the Inference ---
    inf_to_infer = concept_repo.get_concept('final_greeting')
    inf_function = concept_repo.get_concept('greeting_function')
    inf_values = [
        concept_repo.get_concept('input_1'),
        concept_repo.get_concept('input_2'),
        concept_repo.get_concept('prompt_info'),
        concept_repo.get_concept('save_path')
    ]

    inference_entries = [
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_in_composition',
            concept_to_infer=inf_to_infer,
            function_concept=inf_function,
            value_concepts=inf_values,
            flow_info={'flow_index': '1'},
            working_interpretation={
                "paradigm": "thinking_save_and_wrap",
                "value_order": {
                    "prompt_info": 0,
                    "input_1": 1,
                    "input_2": 2,
                    "save_path": 3
                }
            },
        ),
    ]
    
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo

if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Imperative in Composition Orchestrator Demo ===")

    # 1. Create repositories 
    concept_repo, inference_repo = create_imperative_composition_repos()

    # 2. Initialize Body with a base_dir for correct relative path resolution
    current_dir = os.path.dirname(os.path.abspath(__file__))
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
