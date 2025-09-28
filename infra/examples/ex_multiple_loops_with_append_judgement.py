import uuid
import logging
import os
import sys
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import traceback

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

Normcode_new_with_appending = """
{new number pair} | 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1) | 1.1. assigning
        <= $.({new number pair in loop}) 
        <- {new number pair in loop} | 1.1.2. quantifying
            <= *every({number pair}*1)%:[{number}]@(2) | 1.1.2.1. assigning
                <= $.({number pair}*1*2)
                <- {number pair}*1*2
            <- {number pair}*1

        <- {number pair}<$={1}> | 1.1.3. assigning
            <= $+({number pair to append}:{number pair})%:[{number pair}] | 1.1.3.1. timing
                <= @if(<some number is not 0>)

            <- {number pair to append}<$={1}> | 1.1.3.2. quantifying
                <= *every({number pair}*1)%:[{number}]@(3) | 1.1.3.2.1. assigning
                    <= $.({number with last digit removed}) 
                    <- {number with last digit removed} | 1.1.3.2.1.2. imperative
                        <= ::(output 0 if {1}<$({number})%_> is less than 10, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>) 
                        <- {unit place digit}?<:{2}> 
                        <- {number pair}*1*3<:{1}>
                <- {number pair}*1

            <- <some number is not 0> | 1.1.3.3. judgement
                <= :%(False):<{1}<$({number})%_> is 0> | 1.1.3.3.1. timing
                    <= @after({number pair to append}<$={1}>)
                <- {number pair to append}<$={1}><:{1}>
        
    <- {number pair}<$={1}> |ref. %(number pair)=[%(number)=[123, 98]]
"""

# --- Data Definitions ---

def create_appending_repositories_new():
    """Creates concept and inference repositories for the appending scenario."""
    # --- Concept Entries ---
    concept_entries = [
        # --- Ground & Final Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}",
            type="{}",
            axis_name="number pair",
            description="The collection of number pairs.",
            reference_data=[["%(123)", "%(98)"]],
            reference_axis_names=["number pair", "number"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{new number pair}",
            type="{}",
            axis_name="new number pair",
            description="The final collection of new number pairs generated.",
            is_final_concept=True,
        ),
        # The unit place digit concept (result of get operation)
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{unit place digit}?",
            type="{}",
            axis_name="unit place digit",
            context="the digit extracted from the current position",
            description="The extracted digit from the current position",
            reference_data='1 digit counting from the right',
            reference_axis_names=["unit place digit"],
            is_ground_concept=True,
        ),

        # --- Intermediate Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number}",
            type="{}",
            axis_name="number",
            description="An individual number, part of a pair.",
            context="An individual number, part of a pair.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}*1",
            type="{}",
            axis_name="current number pair",
            description="The specific pair of numbers being processed in the current iteration of the outer loop.",
            context="The specific pair of numbers being processed in the current iteration of the outer loop.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}*1*2",
            type="{}",
            axis_name="current number from pair",
            description="The specific number being processed in the current iteration of the inner loop.",
            context="The specific number being processed in the current iteration of the inner loop.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}*1*3",
            type="{}",
            axis_name="current number from pair for appending",
            description="The specific number being processed in the current iteration of the appending loop.",
            context="The specific number being processed in the current iteration of the appending loop.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{new number pair in loop}",
            type="{}",
            axis_name="new number pair in loop",
            description="A new number pair created inside the main loop.",
            context="A new number pair created inside the main loop.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair to append}",
            type="{}",
            axis_name="number pair to append",
            description="A new number pair to be appended to the main collection.",
            context="A new number pair to be appended to the main collection.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number with last digit removed}",
            type="{}",
            axis_name="number with last digit removed",
            description="The number after removing its last digit.",
            context="The number after removing its last digit.",
        ),

        # --- Statement Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="<some number is not 0>",
            type="<>",
            axis_name="some number is not 0",
            description="A boolean concept indicating if some number is not zero.",
        ),

        # --- Function Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every({number pair})%:[{number pair}]@(1)",
            type="*every",
            description="Outer loop quantifier: iterates through each number pair in the collection.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every({number pair}*1)%:[{number}]@(2)",
            type="*every",
            description="Inner loop quantifier: iterates over each number in a pair.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every({number pair}*1)%:[{number}]@(3)",
            type="*every",
            description="Inner loop quantifier for appending: iterates over each number in a pair.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({new number pair in loop})",
            type="$.",
            description="Pass-through function for the new number pair in the loop.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({number pair}*1*2)",
            type="$.",
            description="Pass-through function for an individual number.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$+({number pair to append}:{number pair})",
            type="$+",
            description="Append a new number pair to the main collection.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({number with last digit removed})",
            type="$.",
            description="Pass-through function for the number with last digit removed.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(output 0 if {1}<$({number})%_> is less than 10, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)",
            type="::({})",
            description="Remove the unit place digit from a number.",
            is_ground_concept=True,
            reference_data='::(output 0 if {1}<$({number})%_> is less than 10, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)',
            reference_axis_names=["remove"],
            # is_ground_concept = True,
            is_invariant=True
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name=":%(False):<{1}<$({number})%_> is 0>",
            type="<{}>",
            description="Judgement function to check if a number is not zero.",
            is_ground_concept=True,
            reference_data='::<{1}<$({number})%_> is 0>',
            reference_axis_names=["is_0"],
            is_invariant=True
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@if(<some number is not 0>)",
            type="@if",
            description="Timing condition to check if a non-zero number exists.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@after({number pair to append}<$={1}>)",
            type="@after",
            description="Timing condition to execute after a number pair is ready for appending.",
            is_ground_concept=True,
        ),
    ]
    concept_repo = ConceptRepo(concept_entries)

    # --- Inference Entries ---
    inference_entries = [
        # 1. Main quantifying inference for {new number pair}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('{new number pair}'),
            function_concept=concept_repo.get_concept('*every({number pair})%:[{number pair}]@(1)'),
            value_concepts=[concept_repo.get_concept('{number pair}')],
            context_concepts=[concept_repo.get_concept('{number pair}*1')],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 1,
                    "LoopBaseConcept": "{number pair}",
                    "CurrentLoopBaseConcept": "{number pair}*1",
                    "group_base": "number pair",
                    "InLoopConcept": {},
                    "ConceptToInfer": ["{new number pair}"],
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_with_support_reference_only=True
        ),
        # 1.1. Assigning result of each outer loop iteration
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('*every({number pair})%:[{number pair}]@(1)'),
            function_concept=concept_repo.get_concept('$.({new number pair in loop})'),
            value_concepts=[concept_repo.get_concept('{new number pair in loop}')],
            flow_info={'flow_index': '1.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "{new number pair in loop}",
                    "assign_destination": "*every({number pair})%:[{number pair}]@(1)"
                }
            },
        ),
        # 1.1.2. Quantifying {new number pair in loop}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('{new number pair in loop}'),
            function_concept=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(2)'),
            value_concepts=[concept_repo.get_concept('{number pair}*1')],
            context_concepts=[concept_repo.get_concept('{number pair}*1*2')],
            flow_info={'flow_index': '1.1.2'},
            working_interpretation={
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 2,
                    "LoopBaseConcept": "{number pair}*1",
                    "CurrentLoopBaseConcept": "{number pair}*1*2",
                    "group_base": "number",
                    "InLoopConcept": {},
                    "ConceptToInfer": ["{new number pair in loop}"],
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_with_support_reference_only=True
        ),
        # 1.1.2.1. Assigning value for inner loop
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(2)'),
            function_concept=concept_repo.get_concept('$.({number pair}*1*2)'),
            value_concepts=[concept_repo.get_concept('{number pair}*1*2')],
            flow_info={'flow_index': '1.1.2.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "{number pair}*1*2",
                    "assign_destination": "*every({number pair}*1)%:[{number}]@(2)"
                }
            },
        ),
        # 1.1.3. Appending new pair to {number pair}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{number pair}'),
            function_concept=concept_repo.get_concept('$+({number pair to append}:{number pair})'),
            value_concepts=[
                concept_repo.get_concept('{number pair to append}'),
                concept_repo.get_concept('{number pair}'),
            ],
            flow_info={'flow_index': '1.1.3'},
            working_interpretation={
                "syntax": {
                    "marker": "+",
                    "assign_source": "{number pair to append}",
                    "assign_destination": "{number pair}",
                    "by_axes": ["number pair"]
                }
            },
        ),
        # 1.1.3.1. Timing for appending
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('$+({number pair to append}:{number pair})'),
            function_concept=concept_repo.get_concept('@if(<some number is not 0>)'),
            value_concepts=[concept_repo.get_concept('<some number is not 0>')],
            flow_info={'flow_index': '1.1.3.1'},
            working_interpretation={
                "syntax": {
                    "marker": "if",
                    "condition": "<some number is not 0>"
                }
            }
        ),
        # 1.1.3.2. Quantifying {number pair to append}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('{number pair to append}'),
            function_concept=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(3)'),
            value_concepts=[concept_repo.get_concept('{number pair}*1')],
            context_concepts=[concept_repo.get_concept('{number pair}*1*3')],
            flow_info={'flow_index': '1.1.3.2'},
            working_interpretation={
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 3,
                    "LoopBaseConcept": "{number pair}*1",
                    "CurrentLoopBaseConcept": "{number pair}*1*3",
                    "group_base": "number",
                    "InLoopConcept": {},
                    "ConceptToInfer": ["{number pair to append}"],
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_with_support_reference_only=True
        ),
        # 1.1.3.2.1. Assigning value for the appending loop
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(3)'),
            function_concept=concept_repo.get_concept('$.({number with last digit removed})'),
            value_concepts=[concept_repo.get_concept('{number with last digit removed}')],
            flow_info={'flow_index': '1.1.3.2.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "{number with last digit removed}",
                    "assign_destination": "*every({number pair}*1)%:[{number}]@(3)"
                }
            },
        ),
        # 1.1.3.2.1.2. Imperative step to remove digit
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{number with last digit removed}'),
            function_concept=concept_repo.get_concept('::(output 0 if {1}<$({number})%_> is less than 10, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)'),
            value_concepts=[
                concept_repo.get_concept('{number pair}*1*3'),
                concept_repo.get_concept('{unit place digit}?'),
            ],
            flow_info={'flow_index': '1.1.3.2.1.2'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{number pair}*1*3": 1,
                    "{unit place digit}?": 2,
                }
            },
        ),
        # 1.1.3.3. Judgement for non-zero number
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='judgement',
            concept_to_infer=concept_repo.get_concept('<some number is not 0>'),
            function_concept=concept_repo.get_concept(':%(False):<{1}<$({number})%_> is 0>'),
            value_concepts=[
                concept_repo.get_concept('{number pair to append}'),
            ],
            flow_info={'flow_index': '1.1.3.3'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{number pair to append}": 1
                },
                "condition": "False"
            }
        ),
        # 1.1.3.3.1. Timing for judgement
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept(':%(False):<{1}<$({number})%_> is 0>'),
            function_concept=concept_repo.get_concept('@after({number pair to append}<$={1}>)'),
            value_concepts=[concept_repo.get_concept('{number pair to append}')],
            flow_info={'flow_index': '1.1.3.3.1'},
            working_interpretation={
                "syntax": {
                    "marker": "after",
                    "condition": "{number pair to append}"
                }
            }
        ),
    ]
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo

def log_concept_references(concept_repo, concept_name=None):
    """Helper function to log concept references for debugging purposes.
    
    Args:
        concept_repo: The concept repository to inspect
        concept_name: Optional specific concept name to check. If None, logs all concepts.
    """
    if concept_name:
        # Log specific concept reference
        concept = concept_repo.get_concept(concept_name)
        if concept:
            logging.info(f"Concept found: {concept.concept_name}")
            if concept.concept.reference:
                logging.info(f"  - Reference axes: {concept.concept.reference.axes}")
                logging.info(f"  - Reference shape: {concept.concept.reference.shape}")
                logging.info(f"  - Reference tensor: {concept.concept.reference.tensor}")
            else:
                logging.warning("  - No reference found for concept")
        else:
            logging.error(f"Concept '{concept_name}' not found in repository")
    else:
        # Log all concepts in repository
        logging.info("--- All Concepts in Repository ---")
        for concept in concept_repo.get_all_concepts():
            logging.info(f"  - {concept.concept_name}: {concept.type}")
            if concept.concept.reference:
                logging.info(f"    Reference axes: {concept.concept.reference.axes}")
                logging.info(f"    Reference tensor: {concept.concept.reference.tensor}")
            else:
                logging.info(f"    No reference")


if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Orchestrator Demo ===")

    # 1. Create repositories
    concept_repo, inference_repo = create_appending_repositories_new()

    # 2. Initialize and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        max_cycles=40,
    )

    # 3. Run the orchestrator
    final_concepts = orchestrator.run()

    # 4. Log the final result
    logging.info("--- Final Concepts Returned ---")
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            ref_tensor = final_concept_entry.concept.reference.tensor
            logging.info(f"  - Final Concept '{final_concept_entry.concept_name}': {ref_tensor}")
            print(f"\nFinal concept '{final_concept_entry.concept_name}' tensor: {ref_tensor}")
        else:
            logging.warning(f"No reference found for final concept '{final_concept_entry.concept_name}'.")
            print(f"\nNo reference found for final concept '{final_concept_entry.concept_name}'.")

    logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===") 