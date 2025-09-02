import uuid
import logging
import os
import sys
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Infra Imports ---
try:
    from infra import Inference, Concept, AgentFrame, Reference, BaseStates
    from infra._orchest._blackboard import Blackboard
    from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
    from infra._orchest._waitlist import WaitlistItem, Waitlist
    from infra._orchest._tracker import ProcessTracker
    from infra._orchest._orchestrator import Orchestrator
    from infra._loggers.utils import setup_orchestrator_logging
    from infra._agent._body import Body
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))
    from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Blackboard, Body
    from infra._loggers.utils import setup_orchestrator_logging




# --- Data Definitions ---
def create_sequential_repositories():
    """Creates concept and inference repositories for a waitlist scenario with two intermediate data concepts and three functions."""
    # Create concept entries
    concept_entries = [
        # ConceptEntry(id=str(uuid.uuid4()), concept_name='input_data', type='data', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='intermediate_data_1', type='{}'),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='intermediate_data_2', type='{}'),
        # ConceptEntry(id=str(uuid.uuid4()), concept_name='output_result', type='data', is_final_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='process_function_1', type='::({})'),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='::({1}<$({number})%_> add 1)', type='::({})', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='process_function_3', type='::({})', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='assign_function', type='$.', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='grouping_function', type='&in', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='grouped_data', type='{}'),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='timing_after_1_3', type='@after', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='quant_function', type='*every'),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='items_to_loop*', type='{}'),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='items_to_loop', type='{}', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='output_result_after_quantifying', type='{}', is_final_concept=True),
    ]
    
    # Create concept repository
    concept_repo = ConceptRepo(concept_entries)
    
    # --- Add initial references for ground concepts ---
    logging.info("Assigning initial references to ground concepts for experiment.")
    concept_repo.add_reference('::({1}<$({number})%_> add 1)', "::({1}<$({number})%_> add 1)", axis_names=['add_imperative'])
    concept_repo.add_reference('process_function_3', "Adds ten to the input.", axis_names=['description'])
    concept_repo.add_reference('assign_function', "Assigns a source concept's reference to a destination concept.", axis_names=['description'])
    concept_repo.add_reference('grouping_function', "Groups data based on a context.", axis_names=['description'])
    concept_repo.add_reference('timing_after_1_3', "A timing function that runs after another concept is complete.", axis_names=['description'])
    concept_repo.add_reference('items_to_loop', ["%(101)", "%(102)", "%(103)"], axis_names=['items'])
    # --- End of initial references ---
    
    # --- Inference 1.1.2.2: items_to_loop* -> intermediate_data_1 ---
    inf1_to_infer = concept_repo.get_concept('intermediate_data_1')
    inf1_function = concept_repo.get_concept('process_function_1')
    inf1_values = [concept_repo.get_concept('items_to_loop*')]

    # --- Inference 1.1.2.2.1: timing_after_1_3 => process_function_1 ---
    inf1_1_2_1_to_infer = concept_repo.get_concept('process_function_1')
    inf1_1_2_1_function = concept_repo.get_concept('timing_after_1_3')

    # --- Inference 1.1.2.3: items_to_loop* -> intermediate_data_2 ---
    inf2_to_infer = concept_repo.get_concept('intermediate_data_2')
    inf2_function = concept_repo.get_concept('::({1}<$({number})%_> add 1)')
    inf2_values = [concept_repo.get_concept('items_to_loop*')]

    # --- Inference 1.1: intermediate_data_2 -> quant_function (Assigning) ---
    inf3_to_infer = concept_repo.get_concept('quant_function')
    inf3_function = concept_repo.get_concept('assign_function')
    inf3_values = [concept_repo.get_concept('grouped_data')]

    # --- Inference 1: items_to_loop -> output_result_after_quantifying ---
    inf4_to_infer = concept_repo.get_concept('output_result_after_quantifying')
    inf4_function = concept_repo.get_concept('quant_function')
    inf4_values = [concept_repo.get_concept('items_to_loop')]
    inf4_context = [concept_repo.get_concept('items_to_loop*'), concept_repo.get_concept('intermediate_data_1')]

    # --- Inference 1.1.2: intermediate_data_1 + intermediate_data_2 -> grouped_data ---
    inf_grouping_to_infer = concept_repo.get_concept('grouped_data')
    inf_grouping_function = concept_repo.get_concept('grouping_function')
    inf_grouping_values = [concept_repo.get_concept('intermediate_data_1'), concept_repo.get_concept('intermediate_data_2')]
    inf_grouping_context = [concept_repo.get_concept('items_to_loop*')]


    inference_entries = [
        # Quantifying Inference (Controller)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=inf4_to_infer,
            function_concept=inf4_function,
            value_concepts=inf4_values,
            context_concepts=inf4_context,
            flow_info={'flow_index': '1'},
            working_interpretation={
                "syntax": {
                    "marker": None, 
                    "LoopBaseConcept": "items_to_loop",
                    "ConceptToInfer": ["output_result_after_quantifying"],
                    # "InLoopConcept": {
                    #     "intermediate_data_1": 1
                    # },
                    "completion_status": False,
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_with_support_reference_only=True
        ),
        # --- Inferences inside the loop ---
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=inf3_to_infer,
            function_concept=inf3_function,
            value_concepts=inf3_values,
            flow_info={'flow_index': '1.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "grouped_data",
                    "assign_destination": "quant_function"
                }
            },
        ),
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='simple',
            concept_to_infer=inf1_to_infer,
            function_concept=inf1_function,
            value_concepts=inf1_values,
            flow_info={'flow_index': '1.1.2.2'},
            working_interpretation={},
        ),
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=inf2_to_infer,
            function_concept=inf2_function,
            value_concepts=inf2_values,
            flow_info={'flow_index': '1.1.2.3'},
            working_interpretation={
                "value_order": {
                    "items_to_loop*": 1,
                }
            },
        ),
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=inf1_1_2_1_to_infer,
            function_concept=inf1_1_2_1_function,
            flow_info={'flow_index': '1.1.2.2.1'},
            working_interpretation={
                'syntax': {
                    'marker': 'after',
                    'condition': 'intermediate_data_2'
                }
            },
        ),
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=inf_grouping_to_infer,
            function_concept=inf_grouping_function,
            value_concepts=inf_grouping_values,
            context_concepts=inf_grouping_context,
            flow_info={'flow_index': '1.1.2'},
            working_interpretation={
                "syntax": {
                    "marker": "in"
                }
            },
        ),
    ]
    
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo             

if __name__ == "__main__":
    # Setup file logging with timestamp in logs directory
    log_filename = setup_orchestrator_logging(__file__)
    
    # --- Main Execution Logic ---
    logging.info("=== Starting Orchestrator Demo ===")
    
    # 1. Create repositories 
    concept_repo, inference_repo = create_sequential_repositories()

    # 2. Initialize and run the orchestrator with optional Blackboard and AgentFrameModel
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo, 
        # blackboard=Blackboard(),
        # agent_frame_model="demo",
        # body=Body("qwen-turbo-latest")
    )

    # 3. Run the orchestrator
    final_concepts = orchestrator.run()
    
    logging.info("--- Final Concepts Returned ---")
    if final_concepts:
        for concept in final_concepts:
            ref_tensor = concept.concept.reference.tensor if concept.concept and concept.concept.reference is not None else "N/A"
            logging.info(f"  - {concept.concept_name}: {ref_tensor}")
    else:
        logging.info("  No final concepts were returned.")

    logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===") 