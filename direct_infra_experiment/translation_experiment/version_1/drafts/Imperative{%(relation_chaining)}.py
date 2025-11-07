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
Normcode_SVO_extraction = """
<- [{subject}, {verb}, {object}] | 1.1. imperative
    <= ::(extract the subject, verb, and object from {1}<$({sentence})%_> into {2}?<$({subject})%_>, {3}?<$({verb})%_>, and {4}?<$({object})%_>)
    <- {sentence}<:{1}>
    <- {subject}?<:{2}>
    <- {verb}?<:{3}>
    <- {object}?<:{4}>
"""

Normcode_Analysis = """
<- {analysis_result} | 1. imperative
    <= ::(analyze the relationship between {1}<$({subject})%_> and {2}<$({object})%_>)
    <- [{subject}, {verb}, {object}]<:{1}>
"""


def create_repositories(paragraph_text: str):
    """Creates concept and inference repositories for the SVO extraction scenario."""

    # --- Concept Entries ---
    concept_entries = [
        # --- Final Concept (Relation) ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[{subject}, {verb}, {object}]",
            type="[]",
            context= "relation between subject, verb, and object",
            axis_name="subject, verb, object",
            description="The extracted subject, verb, and object relation.",
            is_final_concept=False,  # No longer the final concept
        ),

        # --- NEW Final Concept ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{analysis_result}",
            type="{}",
            axis_name="analysis_result",
            description="A brief analysis of the relationship between the subject and object.",
            is_final_concept=True,
        ),

        # --- Component output concepts for the relation ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{subject}?",
            type="{}",
            description="The subject of the sentence.",
            reference_data=["The subject of the sentence."],
            reference_axis_names=["_none_axis"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{verb}?",
            type="{}",
            description="The verb of the sentence.",
            reference_data=["The verb of the sentence."],
            reference_axis_names=["_none_axis"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{object}?",
            type="{}",
            description="The object of the sentence.",
            reference_data=["The object of the sentence."],
            reference_axis_names=["_none_axis"],
            is_ground_concept=True,
        ),

        # --- Ground Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{sentence}",
            type="<>",  # statement
            description="The input paragraph containing one or more sentences.",
            reference_data=[paragraph_text],
            reference_axis_names=["sentence"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(extract the subject, verb, and object from {1}<$({sentence})%_> into a relation dict of {2}?<$({subject})%_>, {3}?<$({verb})%_>, and {4}?<$({object})%_>)",
            type="::({})",
            description="An imperative to extract the subject, verb, and object from a sentence into a relation dict.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::(extract the subject, verb, and object from {1}<$({sentence})%_> into a relation dict of {2}?<$({subject})%_>, {3}?<$({verb})%_>, and {4}?<$({object})%_>)"],
            reference_axis_names=["_none_axis"],
        ),

        # --- NEW Imperative Concept ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(analyze the relationship between {1}<$({subject})%_> and {2}<$({object})%_>)",
            type="::({})",
            description="An imperative to analyze the species of the extracted subject.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::(analyze the relationship between {1}<$({subject})%_> and {2}<$({object})%_>)"],
            reference_axis_names=["_none_axis"],
        ),
    ]
    concept_repo = ConceptRepo(concept_entries)

    # --- Inference Entries ---
    inference_entries = [
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('[{subject}, {verb}, {object}]'),
            function_concept=concept_repo.get_concept('::(extract the subject, verb, and object from {1}<$({sentence})%_> into a relation dict of {2}?<$({subject})%_>, {3}?<$({verb})%_>, and {4}?<$({object})%_>)'),
            value_concepts=[
                concept_repo.get_concept('{sentence}'),
                concept_repo.get_concept('{subject}?'),
                concept_repo.get_concept('{verb}?'),
                concept_repo.get_concept('{object}?'),
            ],
            flow_info={'flow_index': '1.1'},
            working_interpretation={
                "is_relation_output": True,
                "with_thinking": True,
                "value_order": {
                    "{sentence}": 1,
                    "{subject}?": 2,
                    "{verb}?": 3,
                    "{object}?": 4,
                }
            },
        ),

        # --- NEW Inference ---
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{analysis_result}'),
            function_concept=concept_repo.get_concept('::(analyze the relationship between {1}<$({subject})%_> and {2}<$({object})%_>)'),
            value_concepts=[
                concept_repo.get_concept('[{subject}, {verb}, {object}]'),
                concept_repo.get_concept('[{subject}, {verb}, {object}]'),
            ],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "with_thinking": True,  # Simple extraction, no complex reasoning needed
                "value_order": {
                    "[{subject}, {verb}, {object}]_1": 1,
                    "[{subject}, {verb}, {object}]_2": 2,
                },
                "value_selectors": {
                    "[{subject}, {verb}, {object}]_1": {
                        "source_concept": "[{subject}, {verb}, {object}]",
                        "index": 0,         # Select the first relation dict in the list
                        "key": "subject"    # Extract the value for the 'subject' key
                    },
                    "[{subject}, {verb}, {object}]_2": {
                        "source_concept": "[{subject}, {verb}, {object}]",
                        "index": 0,
                        "key": "object"
                    }
                }
            },
        ),
    ]
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo


if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Imperative Relation (Subject, Verb, Object Extraction) Demo ===")

    # 1. Create repositories
    paragraph_text = "The cat sat on the mat. A quick brown fox jumps over the lazy dog."
    logging.info(f"Using paragraph: '{paragraph_text}'")

    concept_repo, inference_repo = create_repositories(
        paragraph_text=paragraph_text
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

    logging.info(f"=== Imperative Relation Chaining Demo Complete - Log saved to {log_filename} ===")
    print(f"\n{'='*80}")
    print("PROGRAM COMPLETED")
    print(f"{'='*80}")