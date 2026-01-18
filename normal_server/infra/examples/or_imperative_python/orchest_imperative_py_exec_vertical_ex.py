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


def create_imperative_py_exec_vertical_repos():
    """Creates concept and inference repositories for a vertical Python execution scenario."""
    
    # --- Define file paths ---
    output_filename = "generated_script_prod_vertical.py"
    output_dir = "generated_files"
    script_path = os.path.join(output_dir, output_filename)
    os.makedirs(output_dir, exist_ok=True)

    # 1. --- Create concept entries ---
    concept_entries = [
        ConceptEntry(id=str(uuid.uuid4()), concept_name='script_location', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='input_1', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='input_2', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='py_exec_function', type='::({})', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='execution_result', type='{}', is_final_concept=True),
    ]
    concept_repo = ConceptRepo(concept_entries)
    
    # 2. --- Add initial references for ground concepts ---
    logging.info("Assigning initial references to ground concepts.")
    prompt_template_str = (
        "You are a helpful assistant that writes simple Python code.\\n"
        "Write a Python script that defines a single function named 'main'.\\n"
        "The function should take two arguments, 'input_1' and 'input_2'. It should convert these inputs to integers and return their sum.\\n"
        "Do not include any example usage or calls to the function in the script. "
        "Only provide the function definition inside a JSON object with the keys 'thinking' and 'answer'."
    )
    
    script_location_value = f"%{{script_location}}id({script_path})"

    concept_repo.add_reference('script_location', [script_location_value])
    concept_repo.add_reference('input_1', [f'%381(10)'])
    concept_repo.add_reference('input_2', [f'%a98(12)'])
    # The prompt is provided "vertically" as the reference for the functional concept
    concept_repo.add_reference('py_exec_function', [prompt_template_str])

    # 3. --- Define the Inference ---
    inf_to_infer = concept_repo.get_concept('execution_result')
    inf_function = concept_repo.get_concept('py_exec_function')
    inf_values = [
        concept_repo.get_concept('script_location'),
        concept_repo.get_concept('input_1'),
        concept_repo.get_concept('input_2'),
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
                "paradigm": "v_PromptTemplate-h_ScriptLocation-c_Retrieve_or_GenerateThinkJson_ExtractPy_Execute-o_Normal",
                "value_order": {
                    "script_location": 0,
                    "input_1": 1,
                    "input_2": 2
                }
            },
        ),
    ]
    
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo

if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Imperative Python Execution Orchestrator Demo (Vertical) ===")

    # 1. Create repositories 
    concept_repo, inference_repo = create_imperative_py_exec_vertical_repos()

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
