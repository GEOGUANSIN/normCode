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

Normcode_count = """
{new number pair}| 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1) | 1.1. quantifying
        <= *every({number pair}*1)%:[{number}]@(2) | 1.1.1. assigning
            <= $.({number pair}*1*2)
            <- {number pair}*1*2
        <- {number pair}*1
    <- {number pair} |ref. %(number pair)=[%(number)=[123, 98], [12, 9], [1, 0]]
"""


# --- Data Definitions ---
def create_sequential_repositories():
    """Creates concept and inference repositories for a waitlist scenario with two intermediate data concepts and three functions."""
    # Create concept entries
    concept_entries = [
        # 1. Final Concept: The result of the addition.
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{new number pair}",
            type="{}",
            axis_name="new number pair",
            description="The resulting number pair after the addition process.",
            is_final_concept=True,
        ),
        
        # 2. Ground Concept: The pair of numbers to be added
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}",
            type="{}",
            axis_name="number pair",
            description="The pair of numbers to perform addition on.",
            reference_data=[["%(123)", "%(98)"], ["%(12)", "%(9)"], ["%(1)", "%(0)"]],
            reference_axis_names=["number pair", "number"],
            is_ground_concept=True,
        ),
        
        # 4. Intermediate Concept: The current pair being processed by the outer loop
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}*1",
            type="{}",
            axis_name="current number pair",
            description="The specific pair of numbers being processed in the current iteration of the outer loop.",
        ),

        # 5. Intermediate Concept: The current number being processed by the inner loop
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}*1*2",
            type="{}",
            axis_name="current number from pair",
            description="The specific number being processed in the current iteration of the inner loop.",
        ),

        # 6. Concept for individual number
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number}",
            type="{}",
            axis_name="number",
            description="An individual number, part of a pair.",
        ),

        # --- Quantifier (Function) Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every({number pair})%:[{number pair}]@(1)",
            type="*every",
            description="Outer loop quantifier: iterates through the number pair.",
        ),
        
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every({number pair}*1)%:[{number}]@(2)",
            type="*every",
            description="Inner loop quantifier: iterates over the digits for the current position.",
        ),

        # The dollar function for collection
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({number pair}*1*2)",
            type="$.",
            description="Collect the number from the pair",
            is_ground_concept = True,
        ),
    ]
    
    # Create concept repository
    concept_repo = ConceptRepo(concept_entries)
    # --- End of initial references ---

    inference_entries = [
        # Inference 1: Outer Quantifying Loop for the addition process
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

        # Inference 2: Inner Quantifying Loop to calculate sum at the current position
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('*every({number pair})%:[{number pair}]@(1)'), # This would be updated through the outer loop
            function_concept=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(2)'),
            value_concepts=[concept_repo.get_concept('{number pair}*1')], # Represents the pair of digits
            context_concepts=[
                concept_repo.get_concept('{number pair}*1*2'),
            ],
            flow_info={'flow_index': '1.1'},
            working_interpretation={
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 2,
                    "LoopBaseConcept": "{number pair}*1", # This would be the concept holding the digits for the position
                    "CurrentLoopBaseConcept": "{number pair}*1*2",
                    "group_base": "number",
                    "InLoopConcept": {},
                    "ConceptToInfer": ["*every({number pair})%:[{number pair}]@(1)"], # Placeholder
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_with_support_reference_only=True
        ),

        # Inference 3: Assigning the value for the inner loop
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(2)'),
            function_concept=concept_repo.get_concept('$.({number pair}*1*2)'),
            value_concepts=[
                concept_repo.get_concept('{number pair}*1*2'),
            ],
            flow_info={'flow_index': '1.1.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "{number pair}*1*2",
                    "assign_destination": "*every({number pair}*1)%:[{number}]@(2)"
                }
            },
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
    concept_repo, inference_repo = create_sequential_repositories()

    # 2. Initialize and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        max_cycles=10,
    )

    # 3. Run the orchestrator
    final_concepts = orchestrator.run()

    # 4. Log the final result
    logging.info("--- Final Concepts Returned ---")
    final_concept_entry = next((c for c in final_concepts if c.is_final_concept), None)

    if final_concept_entry and final_concept_entry.concept.reference:
        ref_tensor = final_concept_entry.concept.reference.tensor
        logging.info(f"  - Final Concept '{final_concept_entry.concept_name}': {ref_tensor}")
        print(f"\nFinal concept tensor: {ref_tensor}")
    else:
        logging.warning("No final concept with a reference was returned.")
        print("\nNo final concept with a reference was returned.")

    logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===") 