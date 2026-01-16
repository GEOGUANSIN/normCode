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


def create_imperative_indirect_orchestrator_repos():
    """Creates concept and inference repositories for an imperative_python_indirect orchestrator scenario."""
    
    script_name = "sum_diff_indirect.py"
    script_dir = "generated_scripts"
    script_path = os.path.join(script_dir, script_name)

    prompt_name = "sum_diff_prompt.txt"
    prompt_dir = "generated_prompts"
    prompt_path = os.path.join(prompt_dir, prompt_name)

    # 1. --- Create concept entries ---
    concept_entries = [
        ConceptEntry(id=str(uuid.uuid4()), concept_name='input_1', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='input_2', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='nominalized_action', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='prompt_location', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='nl_instruction', type='::({})', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='output_result', type='{}', is_final_concept=True),
    ]
    concept_repo = ConceptRepo(concept_entries)
    
    # 2. --- Add initial references for ground concepts ---
    logging.info("Assigning initial references to ground concepts.")
    concept_repo.add_reference('input_1', ['%(20)'], axis_names=['number_1'])
    concept_repo.add_reference('input_2', ['%(22)'], axis_names=['number_2'])
    concept_repo.add_reference('nominalized_action', [f"%{{script_location}}({script_path})"], axis_names=['script_location'])
    concept_repo.add_reference('prompt_location', [f"%{{prompt_location}}({prompt_path})"], axis_names=['prompt_location'])
    concept_repo.add_reference('nl_instruction', ['::(get the {_}?<${mean}%> and {_}?<${product}%> of {1}<$({number})%> and {2}<$({number})%>)'], axis_names=['nl_instruction'])

    # 3. --- Define the Inference ---
    inf_to_infer = concept_repo.get_concept('output_result')
    inf_function = concept_repo.get_concept('nl_instruction')
    inf_values = [
        concept_repo.get_concept('input_1'),
        concept_repo.get_concept('input_2'),
        concept_repo.get_concept('nominalized_action'),
        concept_repo.get_concept('prompt_location')
    ]

    inference_entries = [
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_python_indirect',
            concept_to_infer=inf_to_infer,
            function_concept=inf_function,
            value_concepts=inf_values,
            flow_info={'flow_index': '1'},
            working_interpretation={
                "is_relation_output": True,
                "with_thinking": True,
                "value_order": {
                    "input_1": 1,
                    "input_2": 2,
                    "nominalized_action": 3,
                    "prompt_location": 4
                }
            },
        ),
    ]
    
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo

if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Imperative Python Indirect Orchestrator Demo ===")

    examples_dir = os.path.dirname(os.path.dirname(__file__))
    
    # # --- Clean up previous runs ---
    # script_to_generate = os.path.join(examples_dir, "generated_scripts", "sum_diff_indirect.py")
    # if os.path.exists(script_to_generate):
    #     os.remove(script_to_generate)
    #     logging.info(f"Removed existing script at {script_to_generate} to ensure generation.")

    # prompt_to_generate = os.path.join(examples_dir, "generated_prompts", "sum_diff_prompt.txt")
    # if os.path.exists(prompt_to_generate):
    #     os.remove(prompt_to_generate)
    #     logging.info(f"Removed existing prompt at {prompt_to_generate} to ensure saving mechanism is triggered.")

    # 1. Create repositories 
    concept_repo, inference_repo = create_imperative_indirect_orchestrator_repos()

    # 2. Initialize Body with base_dir pointing to the 'examples' directory
    body = Body(llm_name="qwen-turbo-latest", base_dir=examples_dir)

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
