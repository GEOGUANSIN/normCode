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
    here = Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent.parent))
    from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Blackboard, Body
    from infra._loggers.utils import setup_orchestrator_logging


def load_prompt(prompt_name: str) -> str:
    """Loads a prompt from the prompts directory."""
    prompt_path = Path(__file__).parent / "prompts" / prompt_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()

def create_repositories(normtext: str):
    """Creates concept and inference repositories for the translation process."""
    
    # --- Concept Entries ---
    concept_entries = [
        # --- Ground & Final Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normtext}",
            type="{}",
            description="The input natural language text to be translated.",
            reference_data=[[normtext]],
            reference_axis_names=["normtext"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normcode draft}",
            type="{}",
            description="The NormCode script being generated and refined.",
            is_final_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normtext}?",
            type="{}?",
            description="A query for the normtext.",
            is_ground_concept=True,
        ),

        # --- Prompt Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{initialization prompt}",
            type="{}",
            description="Prompt to initialize the NormCode draft from normtext.",
            reference_data=[[load_prompt("initialization_prompt")]],
            reference_axis_names=["prompt"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{completion check prompt}",
            type="{}",
            description="Prompt to check if the NormCode draft is complete.",
            reference_data=[[load_prompt("completion_check_prompt")]],
            reference_axis_names=["prompt"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{concept identification prompt}",
            type="{}",
            description="Prompt to identify the next concept to decompose.",
            reference_data=[[load_prompt("concept_identification_prompt")]],
            reference_axis_names=["prompt"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{question inquiry prompt}",
            type="{}",
            description="Prompt to formulate a question about the concept to decompose.",
            reference_data=[[load_prompt("question_inquiry_prompt")]],
            reference_axis_names=["prompt"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{operator selection prompt}",
            type="{}",
            description="Prompt to select the appropriate NormCode operator.",
            reference_data=[[load_prompt("operator_selection_prompt")]],
            reference_axis_names=["prompt"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{children concept creation prompt}",
            type="{}",
            description="Prompt to create child concepts for the new inference.",
            reference_data=[[load_prompt("children_concept_creation_prompt")]],
            reference_axis_names=["prompt"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normtext distribution prompt}",
            type="{}",
            description="Prompt to distribute normtext to child concepts.",
            reference_data=[[load_prompt("normtext_distribution_prompt")]],
            reference_axis_names=["prompt"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normcode draft update prompt}",
            type="{}",
            description="Prompt to update the NormCode draft with the new inference.",
            reference_data=[[load_prompt("normcode_draft_update_prompt")]],
            reference_axis_names=["prompt"],
            is_ground_concept=True,
        ),

        # --- Intermediate Concepts ---
        ConceptEntry(id=str(uuid.uuid4()), concept_name="<normcode draft is complete>", type="<>", description="Flag indicating if the translation is finished."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="[{concept to decomposed} and {remaining normtext}]", type="[]", description="The concept to be decomposed and the remaining normtext."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{concept to decomposed}", type="{}", description="The specific concept snippet selected for decomposition."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{remaining normtext}", type="{}", description="The portion of the normtext associated with the concept to be decomposed."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="[{question} and {question type}]", type="[]", description="The question formulated for the decomposition and its type."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{question}", type="{}", description="The question about how to decompose the concept."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{question type}", type="{}", description="The type of the question (e.g., Methodology, Classification)."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{functional concept}", type="{}", description="The selected NormCode operator for the decomposition."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{children concepts}", type="{}", description="The newly created child concepts."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{new inference}", type="{}", description="The newly generated inference to be added to the draft."),
        
        # --- Versioned/Identified Concepts ---
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{normtext}<$={1}>", type="{}", description="Identified instance of normtext."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{normcode draft}<$={1}>", type="{}", description="First version of the normcode draft."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{normcode draft}<$={2}>", type="{}", description="Normcode draft instance for the main loop."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="{normcode draft}<$={3}>", type="{}", description="Updated normcode draft from the loop body."),

        # --- Functional Concepts ---
        ConceptEntry(id=str(uuid.uuid4()), concept_name="$.({normcode draft})", type="$.", description="Specification for the final normcode draft."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name=":>:{normtext}?()", type=":>:", description="Input operator for normtext."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="::{%(direct)}({initialization prompt}: {1}<$({normtext})%>)", type="::", description="Imperative to initialize the draft."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="*every({normcode draft})", type="*every", description="Main loop that iterates on the draft until completion."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="::{completion check prompt}<{1}<$({normcode draft})%> is a complete>", type="::", description="Imperative to check for completion."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="$={1}", type="$=", description="Identity assignment."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="@before({normcode draft}<$={2}>)", type="@before", description="Timing operator to execute before."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="$={3}", type="$=", description="Identity assignment."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="@if!(<{normcode draft} is complete>)", type="@if!", description="Executes if draft is not complete."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="::{%(direct)}({concept identification prompt}<$(prompt)%>: {1}<$({normcode draft})%>)", type="::", description="Imperative for concept identification."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="::{%(direct)}({question inquiry prompt}<$(prompt)%>: {1}<$({concept to decomposed})%>, {2}<$({remaining normtext})%>)", type="::", description="Imperative for question inquiry."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="::{%(direct)}({operator selection prompt}<$(prompt)%>: {1}<$({question})%>, {2}<$({concept to decomposed})%>, {3}<$({question type})%>, {4}<$({remaining normtext})%>)", type="::", description="Imperative for operator selection."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="::{%(direct)}({children concept creation prompt}<$(prompt)%>: {1}<$({functional concept})%>, {2}<$({question})%>, {3}<$({concept to decomposed})%>, {4}<$({question type})%>, {5}<$({remaining normtext})%>)", type="::", description="Imperative for children concept creation."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="::{%(direct)}({normtext distribution prompt}<$(prompt)%>: {1}<$({functional concept})%>, {2}<$({children concepts})%>, {3}<$({concept to decomposed})%>, {4}<$({remaining normtext})%>)", type="::", description="Imperative for normtext distribution."),
        ConceptEntry(id=str(uuid.uuid4()), concept_name="::{%(direct)}({normcode draft update prompt}<$(prompt)%>: {1}<$({normcode draft})%>, {2}<$({new inference})%>)", type="::", description="Imperative for updating the normcode draft."),
    ]
    concept_repo = ConceptRepo(concept_entries)

    # --- Inference Entries ---
    # TODO: Add inference entries here
    inference_entries = []
    
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the NormCode self-translation orchestrator.")
    parser.add_argument("normtext_file", type=str, help="Path to the file containing the normtext to translate.")
    parser.add_argument("--max-cycles", type=int, default=50, help="Maximum number of cycles for the orchestrator to run.")
    
    args = parser.parse_args()

    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting NormCode Self-Translation Orchestrator ===")

    # 1. Load normtext
    normtext_path = Path(args.normtext_file)
    if not normtext_path.exists():
        print(f"Error: Normtext file not found at {normtext_path}")
        sys.exit(1)
    normtext_content = normtext_path.read_text()
    logging.info(f"Loaded normtext from: {normtext_path}")

    # 2. Create repositories
    try:
        concept_repo, inference_repo = create_repositories(normtext_content)
    except FileNotFoundError as e:
        logging.error(str(e))
        print(f"Error: {e}")
        sys.exit(1)

    # 3. Initialize and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        max_cycles=args.max_cycles,
    )

    # 4. Run the orchestrator
    final_concepts = orchestrator.run()

    # 5. Log the final result
    logging.info("--- Final Concepts Returned ---")
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            ref_tensor = final_concept_entry.concept.reference.tensor
            logging.info(f"  - Final Concept '{final_concept_entry.concept_name}': {ref_tensor}")
            print(f"\nFinal concept '{final_concept_entry.concept_name}' tensor: {ref_tensor}")
            if final_concept_entry.concept_name == "{normcode draft}":
                print("\n--- FINAL NORMCODE DRAFT ---")
                # Assuming the result is in the tensor
                final_draft = ref_tensor[0] if isinstance(ref_tensor, list) and ref_tensor else ref_tensor
                print(final_draft)
                print("--------------------------")

        else:
            logging.warning(f"No reference found for final concept '{final_concept_entry.concept_name}'.")
            print(f"\nNo reference found for final concept '{final_concept_entry.concept_name}'.")

    logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===")
    print(f"\n{'='*80}")
    print("PROGRAM COMPLETED")
    print(f"{'='*80}")
