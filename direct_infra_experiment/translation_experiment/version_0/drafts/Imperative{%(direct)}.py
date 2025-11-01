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
:<:({normcode draft}) | 1. imperative
    <= ::{%(direct)}({initialization prompt}<$({prompt})%>: {1}<$({normtext})%>)
    <- {initialization prompt}<:{prompt}>
        |%{prompt_location}: initialization_prompt
    <- {normtext}<$={1}><:{1}>
"""


def create_repositories(norm_text: str):
    """Creates concept and inference repositories for the direct imperative scenario."""
    
        
    # Path to the prompt file. Using resolve() to make it an absolute path.
    prompt_file_path = Path(__file__).parent.parent / "prompts" / "initialization_prompt"
    prompt_location_string = f"%{{prompt}}({prompt_file_path.resolve()})"
    normtext_string = f"%({norm_text})"
    
    # --- Concept Entries ---
    concept_entries = [
        # --- Ground & Final Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normcode draft}",
            type="<>",
            axis_name="normcode draft",
            description="The final normcode draft.",
            is_final_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(direct)}({prompt}:{1})",
            type="::({})",
            description="A direct imperative to generate normcode.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::{%(direct)}({prompt}:{1})"],
            reference_axis_names=["direct imperative"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{initialization prompt}",
            type="{}",
            axis_name="initialization_prompt",
            description="The specification for the prompt, including its location.",
            reference_data=[prompt_location_string],
            reference_axis_names=["initialization_prompt"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normtext}",
            type="{}",
            axis_name="normtext",
            description="The input normtext for the draft.",
            reference_data=[normtext_string],
            reference_axis_names=["normtext"],
            is_ground_concept=True,
        ),
    ]
    concept_repo = ConceptRepo(concept_entries)

    # --- Inference Entries ---
    inference_entries = [
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_direct',
            concept_to_infer=concept_repo.get_concept('{normcode draft}'),
            function_concept=concept_repo.get_concept('::{%(direct)}({prompt}:{1})'),
            value_concepts=[
                concept_repo.get_concept('{initialization prompt}'),
                concept_repo.get_concept('{normtext}')
            ],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{initialization prompt}": 0,
                    "{normtext}": 1,
                }
            },
        ),
    ]
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo


if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Direct Imperative Demo ===")

    # 1. Create repositories
    norm_text = "Love is a deep feeling of care and attachment toward someone or something. It shows through kind acts, sacrifice, and caring about another person's happiness. Love can be between partners, family, friends, or even spiritual connections. Love means accepting someone and wanting them to be happy, even when it's hard. Love is both an emotion and a decision to put someone else's wellbeing first."
    logging.info(f"Using normtext: {norm_text}")

    concept_repo, inference_repo = create_repositories(
        norm_text=norm_text
    )

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
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            ref_tensor = final_concept_entry.concept.reference.tensor
            logging.info(f"  - Final Concept '{final_concept_entry.concept_name}': {ref_tensor}")
            print(f"\nFinal concept '{final_concept_entry.concept_name}' tensor: {ref_tensor}")
        else:
            logging.warning(f"No reference found for final concept '{final_concept_entry.concept_name}'.")
            print(f"\nNo reference found for final concept '{final_concept_entry.concept_name}'.")

    logging.info(f"=== Direct Imperative Demo Complete - Log saved to {log_filename} ===")
    print(f"\n{'='*80}")
    print("PROGRAM COMPLETED")
    print(f"{'='*80}")