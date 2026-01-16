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

Normcode_new_appending = """
{number pair}<$={1}>
    <= $+({number pair to append}:{number pair})%:[{number pair}] 
    <- {number pair to append} |ref. %(number)=[1, 0]
    <- {number pair}<$={1}> |ref. %(number pair)=[%(number)=[123, 98], [12, 9]]
"""

# --- Data Definitions ---
def create_appending_repositories():
    """Creates concept and inference repositories for the appending scenario."""
    # Create concept entries
    concept_entries = [
        # 1. The collection of number pairs. This is both a ground and final concept.
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}",
            type="{}",
            axis_name="number pair",
            description="The collection of number pairs.",
            reference_data=[["%(123)", "%(98)"], ["%(12)", "%(9)"]],
            reference_axis_names=["number pair", "number"],
            is_ground_concept=True,
            is_final_concept=True,
        ),

        # 2. The number pair to append. This is a ground concept.
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair to append}",
            type="{}",
            axis_name="number pair to append",
            description="The number pair to append to the collection.",
            reference_data=["%(1)", "%(0)"],
            reference_axis_names=["some number pair"],
            is_ground_concept=True,
        ),

        # 3. The append function concept.
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$+({number pair to append}:{number pair})",
            type="$+",
            description="Append the new number pair to the collection.",
            is_ground_concept=True,
        ),
        
        # 4. Concept for individual number
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number}",
            type="{}",
            axis_name="number",
            description="An individual number, part of a pair.",
        ),
    ]

    # Create concept repository
    concept_repo = ConceptRepo(concept_entries)

    inference_entries = [
        # Inference for appending the number pair
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{number pair}'),
            function_concept=concept_repo.get_concept('$+({number pair to append}:{number pair})'),
            value_concepts=[
                concept_repo.get_concept('{number pair to append}'),
                concept_repo.get_concept('{number pair}'),
            ],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "syntax": {
                    "marker": "+",
                    "assign_source": "{number pair to append}",
                    "assign_destination": "{number pair}",
                    "by_axes": ["number pair"]
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
    concept_repo, inference_repo = create_appending_repositories()

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