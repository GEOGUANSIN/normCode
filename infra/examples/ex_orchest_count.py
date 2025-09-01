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



# --- Normcode for this example ---

Normcode_count = """
[all {index} and {digit} of number] | 1. quantifying
    <= *every({number})%:[{number}]@[{index}^1] | 1.1. assigning
        <= $.([{index} and {digit}]*) 
        <- [{index} and {digit}]* | 1.1.2. grouping
            <= &in({index}*;{digit}*) 
            <- {index}*
            <- {digit}* | 1.1.2.3. imperative/simple
                <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>) 
                <- {unit place digit}?<:{2}>
                <- {number}*<:{2}>
        <- {number}<:{1}> | 1.1.3. assigning
            <= $+({new number}:{number}) 
            <- {new number} | 1.1.3.2. imperative/simple
                <= ::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>) 
                     <= @after([{index} and {digit}]*) | 1.1.3.2.1. timing
                <- {unit place digit}?<:{2}> 
                <- {number}*<:{2}>
        <- {index}* | 1.1.4. imperative/simple
            <= ::(increment {1}<$({index})%_>) | 1.1.4.1. timing
                <= @after([{index} and {digit}]*) 
            <- {index}*
    <- {number}<:{1}>
"""


# --- Data Definitions ---
def create_sequential_repositories(number: str = "123"):
    """Creates concept and inference repositories for a waitlist scenario with two intermediate data concepts and three functions."""
    # Create concept entries
    concept_entries = [
        # Main concept to be inferred - the result of the quantification
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[all {index} and {digit} of number]",
            type="{}",
            description="Extract all digits from a number with their positions",
            is_final_concept=True,
        ),
        
        # The number to process
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number}",
            type="{}",
            description="The input number to extract digits from",
            reference_data=[f"%({number})"],
            reference_axis_names=["{number}"],
            is_ground_concept=True,
        ),
    
        # The grouping concept for index and digit pairs
            ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[{index} and {digit}]*",
            type="[]",
            description="Collection of index-digit pairs",
        ),
        

        # The number concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number}*",
            type="{}",
            description="The number to process under quantifying",
        ),

        # The index concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{index}*",
            type="{}",
            description="Current position index in the number",
            reference_data='1',
            reference_axis_names=["{index}"],
            is_ground_concept=True,
        ),
        
        # The digit concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{digit}*",
            type="{}",
            description="The digit extracted from the current position",
        ),
        
        # The unit place digit concept (result of get operation)
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{unit place digit}?",
            type="{}",
            description="The extracted digit from the current position",
            reference_data='1 digit counting from the right',
            reference_axis_names=["{unit place digit}"],
            is_ground_concept=True,
        ),
        
        # The new number concept (result of remove operation)
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{new number}",
            type="{}",
            description="The number with the current digit removed",
        ),
        
        # The increment function for index
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(increment {1}<$({index})%_>)",
            type="::()",
            description="Increment the index counter",
            reference_data='::(increment {1}<$({index})%_>)',
            reference_axis_names=["increment"],
            # is_ground_concept = True,
        ),
        
        # The get digit function
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)",
            type="::()",
            description="Extract the rightmost digit from a number",
            reference_data='::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)',
            reference_axis_names=["get"],
            is_ground_concept = True,
        ),
        
        # The remove digit function
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)",
            type="::()",
            description="Remove the rightmost digit from a number",
            reference_data='::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)',
            reference_axis_names=["remove"],
            # is_ground_concept = True,
        ),
        
        # The quantifier function
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every({number})%:[{number}]@[{index}^1]",
            type="*every",
            description="Quantifier that processes each digit of the number",
        ),
        
        # The add function for new number
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$+({new number}:{number})",
            type="$+",
            description="Add the new number to the collection",
            is_ground_concept = True,
        ),

        # The dollar function for collection
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.([{index} and {digit}]*)",
            type="$.",
            description="Collect the index-digit pairs",
            is_ground_concept = True,
        ),
        
        # The timing concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@after([{index} and {digit}]*)",
            type="@after",
            description="Execute after the index-digit pair is processed",
            is_ground_concept = True,
        ),
        
        # The in relation for grouping
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="&in({index}*;{digit}*)",
            type="&in",
            description="Group index and digit together",
            is_ground_concept = True,
        ),
        
    ]
    
    # Create concept repository
    concept_repo = ConceptRepo(concept_entries)
    # --- End of initial references ---

    inference_entries = [

        # Quantifying Inference (Syntactic)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('[all {index} and {digit} of number]'),
            function_concept=concept_repo.get_concept('*every({number})%:[{number}]@[{index}^1]'),
            value_concepts=[concept_repo.get_concept('{number}')],
            context_concepts=[concept_repo.get_concept('{index}*'), concept_repo.get_concept('[{index} and {digit}]*'), concept_repo.get_concept('{number}*')],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "syntax": {
                    "marker": "every", 
                    "LoopBaseConcept": "{number}",
                    "InLoopConcept": {
                        "{index}*": 1,
                    },
                    "ConceptToInfer": ["[all {index} and {digit} of number]"],
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_with_support_reference_only=True
        ),

        # --- Inferences inside the loop ---
        # Assigning Inference (Syntactic)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('*every({number})%:[{number}]@[{index}^1]'),
            function_concept=concept_repo.get_concept('$.([{index} and {digit}]*)'),
            value_concepts=[concept_repo.get_concept('[{index} and {digit}]*'), concept_repo.get_concept('{number}'), concept_repo.get_concept('{index}*')],
            flow_info={'flow_index': '1.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "[{index} and {digit}]*",
                    "assign_destination": "*every({number})%:[{number}]@[{index}^1]"
                }
            },
        ),

        # Grouping Inference (Syntactic)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=concept_repo.get_concept('[{index} and {digit}]*'),
            function_concept=concept_repo.get_concept('&in({index}*;{digit}*)'),
            value_concepts=[concept_repo.get_concept('{index}*'), concept_repo.get_concept('{digit}*')],
            context_concepts=[concept_repo.get_concept('{index}*'), concept_repo.get_concept('{digit}*')],
            flow_info={'flow_index': '1.1.2'},
            working_interpretation={
                "syntax": {
                    "marker": "in",
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{digit}*'),
            function_concept=concept_repo.get_concept('::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)'),
            value_concepts=[concept_repo.get_concept('{number}*'), concept_repo.get_concept('{unit place digit}?')],
            flow_info={'flow_index': '1.1.2.3'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{number}*": 1,
                    "{unit place digit}?": 2,
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{number}'),
            function_concept=concept_repo.get_concept('$+({new number}:{number})'),
            value_concepts=[concept_repo.get_concept('{new number}')],
            flow_info={'flow_index': '1.1.3'},
            working_interpretation={
                "syntax": {
                    "marker": "+",
                    "assign_source": "{new number}",
                    "assign_destination": "{number}"
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{new number}'),
            function_concept=concept_repo.get_concept('::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)'),
            value_concepts=[concept_repo.get_concept('{unit place digit}?'), concept_repo.get_concept('{number}*')],
            flow_info={'flow_index': '1.1.3.2'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{number}*": 1,
                    "{unit place digit}?": 2,
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)'),
            function_concept=concept_repo.get_concept('@after([{index} and {digit}]*)'),
            value_concepts=[concept_repo.get_concept('@after([{index} and {digit}]*)')],
            flow_info={'flow_index': '1.1.3.2.1'},
            working_interpretation={
                'syntax': {
                    'marker': 'after',
                    'condition': '[{index} and {digit}]*'
                }
            },
            start_without_value=True,
            start_without_function=True
        ),
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{index}*'),
            function_concept=concept_repo.get_concept('::(increment {1}<$({index})%_>)'),
            value_concepts=[concept_repo.get_concept('{index}*')],
            flow_info={'flow_index': '1.1.4'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": False,
                "value_order": {
                    "{index}*": 1,
                }
            },
        ),

        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('::(increment {1}<$({index})%_>)'),
            function_concept=concept_repo.get_concept('@after([{index} and {digit}]*)'),
            value_concepts=[concept_repo.get_concept('@after([{index} and {digit}]*)')],
            flow_info={'flow_index': '1.1.4.1'},
            working_interpretation={
                'syntax': {
                    'marker': 'after',
                    'condition': '[{index} and {digit}]*'
                }
            },
            start_without_value=True,
            start_without_function=True
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
        max_cycles=20,
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