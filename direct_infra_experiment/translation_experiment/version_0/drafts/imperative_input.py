import uuid
import logging
import os
import sys
import argparse
from pathlib import Path

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
    # If infra is not in the path, add it.
    # This is for running the script directly.
    # Need to go up 4 levels from here to reach project root where infra/ is located:
    # drafts -> version_0 -> translation_experiment -> direct_infra_experiment -> normCode (project root)
    here = Path(__file__).parent
    project_root = here.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    from infra import Inference, Concept, AgentFrame, Reference, BaseStates
    from infra._orchest._blackboard import Blackboard
    from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
    from infra._orchest._waitlist import WaitlistItem, Waitlist
    from infra._orchest._tracker import ProcessTracker
    from infra._orchest._orchestrator import Orchestrator
    from infra._loggers.utils import setup_orchestrator_logging
    from infra._agent._body import Body


# --- Normcode for this example ---
Normcode_v0_manual = """
:<:({normtext}) | 1. imperative (input)
    <= :>:({prompt}<:{normtext}>)
    <- {normtext}?<:{prompt}>
        |%{prompt_location}: normtext_prompt
"""


def create_repositories():
    """Creates concept and inference repositories for the imperative_input scenario."""
    
    # Path to the prompt file. Using resolve() to make it an absolute path.
    # Based on the NormCode annotation |%{prompt_location}: normtext_prompt
    prompt_file_path = Path(__file__).parent.parent / "prompts" / "normtext_prompt"
    prompt_location_string = f"%{{prompt}}({prompt_file_path.resolve()})"
    
    # --- Concept Entries ---
    concept_entries = [
        # --- Final Concept (output) ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normtext}",
            type="{}",
            axis_name="normtext",
            description="The normtext input collected from the user.",
            is_final_concept=True,
        ),
        # --- Functional Concept (input operation) ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name=":>:({prompt}<:{normtext}>)",
            type=":>:()",
            description="An input operation to collect normtext from the user.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=[":>:({prompt}<:{normtext}>)"],
            reference_axis_names=["input operation"],
        ),
        # --- Value Concept (contains prompt location) ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normtext}?",
            type="{}",
            axis_name="normtext",
            description="The prompt specification for collecting normtext, including its location.",
            reference_data=[prompt_location_string],
            reference_axis_names=["normtext"],
            is_ground_concept=True,
        ),
    ]
    concept_repo = ConceptRepo(concept_entries)

    # --- Inference Entries ---
    inference_entries = [
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_input',
            concept_to_infer=concept_repo.get_concept('{normtext}'),
            function_concept=concept_repo.get_concept(':>:({prompt}<:{normtext}>)'),
            value_concepts=[
                concept_repo.get_concept('{normtext}?')
            ],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "value_order": {
                    "{normtext}?": 1,
                }
            },
        ),
    ]
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo


if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Imperative Input Demo ===")
    logging.info("This demo will prompt the user for normtext input.")

    # 1. Create repositories
    concept_repo, inference_repo = create_repositories()

    # 2. Initialize and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        max_cycles=10,
    )

    # 3. Run the orchestrator
    # This will trigger the imperative_input sequence, which will prompt the user for input
    final_concepts = orchestrator.run()

    # 4. Log the final result
    logging.info("--- Final Concepts Returned ---")
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            ref_tensor = final_concept_entry.concept.reference.tensor
            logging.info(f"  - Final Concept '{final_concept_entry.concept_name}': {ref_tensor}")
            print(f"\nFinal concept '{final_concept_entry.concept_name}':")
            print(f"  Value: {ref_tensor}")
        else:
            logging.warning(f"No reference found for final concept '{final_concept_entry.concept_name}'.")
            print(f"\nNo reference found for final concept '{final_concept_entry.concept_name}'.")

    logging.info(f"=== Imperative Input Demo Complete - Log saved to {log_filename} ===")
    print(f"\n{'='*80}")
    print("PROGRAM COMPLETED")
    print(f"{'='*80}")