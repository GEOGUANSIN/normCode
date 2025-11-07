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
:<:({a}) | 1. assignment

    <= $.({a}<$={1}>) 

    <- [all {a}]<$={1}> | 1.2. grouping
        <= &across({a})
        <- {a}<$={1}>
            |%: 3
    
    <- {a}<$={1}> | 1.3. quantifying
        <= *every([all {a}]<$={1}>)@(1) | 1.3.1. assignment

            <= $.({a}<$={#}>) 

            <- <a>5> | 1.3.1.2. judgement
                <= ::{%(all True)}<{1}<$({number})%_> > 5>
                <- [all {a}]<$={1}>*1<:{1}>

            <- {a}<$={2}>  | 1.3.1.3. assignment
                <= $.([all {a}]<$={1}>*1) | 1.3.1.3.1. timing
                    <= @if(<a>5>)
                    <- <a>5>
                <- [all {a}]<$={1}>*1

            <- {a}<$={3}> | 1.3.1.4. imperative
                <= ::({1}<$({number})%> += 1) | 1.3.1.4.1. timing
                    <= @if!(<a>5>)
                    <- <a>5>
                <- [all {a}]<$={1}>*1<:{1}>

            <- [all {a}]<$={1}> | 1.3.1.5. grouping
                <= &across({a})
                <- {a}<$={2}> 
                <- {a}<$={3}>

        <- [all {a}]<$={1}>
"""


def create_repositories():
    """Creates concept and inference repositories for a pre-loop assignment scenario."""
    concept_entries = [
        # Ground Concepts
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{a}<$={1}>",
            type="{}",
            description="A single number.",
            axis_name="value",
            is_ground_concept=True,
            reference_data=["%(4)"],
            reference_axis_names=["value"],
        ),

        # Inferred Concepts
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{a}",
            type="{}",
             axis_name="value",
            description="Final output concept.",
            is_final_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[all {a}]<$={1}>",
            type="[]",
            axis_name="value",
            description="A collection of {a}<$={1}>.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{a}<$={2}>",
            type="{}",
            axis_name="value",
            description="The destination draft, to be inferred within the loop.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="<a>5>",
            type="<>",
            description="Judgement result, true if current item is 5.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{a}<$={3}>",
            type="{}",
            axis_name="value",
            description="Result of imperative operation.",
        ),

        # Functional Concepts
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({a}<$={1}>)",
            type="$.",
            description="Assignment from {a}<$={1}>.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="&across({a})",
            type="&across",
            description="Grouping function.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every([all {a}]<$={1}>)@(1)",
            type="*every",
            description="The quantifier for the main loop.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({a}<$={#}>)",
            type="$.",
            description="Assignment to {a}<$={#}>.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(all True)}<{1}<$({number})%_> > 5>",
            type="<{}>",
            description="Judgement function to check if value is > 5.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::{%(all True)}<{1}<$({number})%_> > 5>"],
            reference_axis_names=["is_greater_than_5"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.([all {a}]<$={1}>*1)",
            type="$.",
            description="Assignment to loop item.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::({1}<$({number})%> += 1)",
            type="::",
            description="Imperative function to increment value.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::({1}<$({number})%> += 1)"],
            reference_axis_names=["_none_axis"],
        ),

        # Timing Concepts
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@if(<a>5>)",
            type="@if",
            description="Conditional execution if <a>5> is true.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@if!(<a>5>)",
            type="@if!",
            description="Conditional execution if <a>5> is false.",
            is_ground_concept=True,
        ),

        # Loop Item Concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[all {a}]<$={1}>*1",
            type="[]",
            description="The current item from the number sequence in a loop.",
        ),
    ]
    concept_repo = ConceptRepo(concept_entries)

    # --- Inference Entries ---
    inference_entries = [
        # Final Assignment
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{a}'),
            function_concept=concept_repo.get_concept('$.({a}<$={1}>)'),
            value_concepts=[
                concept_repo.get_concept('{a}<$={1}>')
            ],
            flow_info={'flow_index': '1'},
            working_interpretation={"syntax": {"marker": ".", "assign_source": "{a}<$={1}>", "assign_destination": "{a}"}}
        ),

        # Grouping
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=concept_repo.get_concept('[all {a}]<$={1}>'),
            function_concept=concept_repo.get_concept('&across({a})'),
            value_concepts=[concept_repo.get_concept('{a}<$={1}>')],
            flow_info={'flow_index': '1.2'},
            working_interpretation={"syntax": {"marker": "across", "by_axis_concepts": "{a}<$={1}>"}}
        ),

        # Quantifying (Main Loop)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('{a}<$={1}>'),
            function_concept=concept_repo.get_concept('*every([all {a}]<$={1}>)@(1)'),
            value_concepts=[concept_repo.get_concept('[all {a}]<$={1}>')],
            context_concepts=[concept_repo.get_concept('[all {a}]<$={1}>*1')],
            flow_info={'flow_index': '1.3'},
            working_interpretation={
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 1,
                    "LoopBaseConcept": "[all {a}]<$={1}>",
                    "CurrentLoopBaseConcept": "[all {a}]<$={1}>*1",
                    "group_base": "a",
                    "InLoopConcept": {},
                    "ConceptToInfer": ["{a}<$={1}>", "[all {a}]<$={1}>"]
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_without_support_reference_only_once=True
        ),

        # Assignment inside loop
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('*every([all {a}]<$={1}>)@(1)'),
            function_concept=concept_repo.get_concept('$.({a}<$={#}>)'),
            value_concepts=[
                concept_repo.get_concept('[all {a}]<$={1}>'),
                concept_repo.get_concept('{a}<$={2}>'),
                concept_repo.get_concept('{a}<$={3}>'),
                concept_repo.get_concept('<a>5>'),
                ],
            flow_info={'flow_index': '1.3.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": ["{a}<$={3}>","{a}<$={2}>"],
                    "assign_destination": "*every([all {a}]<$={1}>)@(1)"
                }
            }
        ),


        # Judgement
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='judgement',
            concept_to_infer=concept_repo.get_concept('<a>5>'),
            function_concept=concept_repo.get_concept('::{%(all True)}<{1}<$({number})%_> > 5>'),
            value_concepts=[concept_repo.get_concept('[all {a}]<$={1}>*1')],
            flow_info={'flow_index': '1.3.1.2'},
            working_interpretation={
                "is_relation_output": False, "with_thinking": True, "condition": "True",
                "value_order": {"[all {a}]<$={1}>*1": 1}
            }
        ),

        # Conditional Assignment
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{a}<$={2}>'),
            function_concept=concept_repo.get_concept('$.([all {a}]<$={1}>*1)'),
            value_concepts=[
                concept_repo.get_concept('[all {a}]<$={1}>*1'),
                concept_repo.get_concept('<a>5>')
            ],
            flow_info={'flow_index': '1.3.1.3'},
            working_interpretation={
                "syntax": {
                    "marker": ".", "assign_source": "[all {a}]<$={1}>*1", "assign_destination": "{a}<$={2}>",
                }
            }
        ),

        # Timing for Conditional Assignment
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('$.([all {a}]<$={1}>*1)'),
            function_concept=concept_repo.get_concept('@if(<a>5>)'),
            value_concepts=[concept_repo.get_concept('<a>5>')],
            flow_info={'flow_index': '1.3.1.3.1'},
            working_interpretation={
                "syntax": {
                    "marker": "if",
                    "condition": "<a>5>"
                }
            }
        ),

        # Imperative
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{a}<$={3}>'),
            function_concept=concept_repo.get_concept('::({1}<$({number})%> += 1)'),
            value_concepts=[
                concept_repo.get_concept('[all {a}]<$={1}>*1'),
                concept_repo.get_concept('<a>5>')
            ],
            flow_info={'flow_index': '1.3.1.4'},
            working_interpretation={
                "is_relation_output": False, "with_thinking": True,
                "value_order": {"[all {a}]<$={1}>*1": 1}
            }
        ),

        # Timing for Imperative
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('::({1}<$({number})%> += 1)'),
            function_concept=concept_repo.get_concept('@if!(<a>5>)'),
            value_concepts=[concept_repo.get_concept('<a>5>')],
            flow_info={'flow_index': '1.3.1.4.1'},
            working_interpretation={
                "syntax": {
                    "marker": "if!",
                    "condition": "<a>5>"
                }
            }
        ),

        # Grouping inside loop
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=concept_repo.get_concept('[all {a}]<$={1}>'),
            function_concept=concept_repo.get_concept('&across({a})'),
            value_concepts=[
                concept_repo.get_concept('{a}<$={2}>'),
                concept_repo.get_concept('{a}<$={3}>')
            ],
            flow_info={'flow_index': '1.3.1.5'},
            working_interpretation={"syntax": {"marker": "across", "by_axis_concepts": ["{a}<$={2}>", "{a}<$={3}>"]}}
        ),
    ]
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo


if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting @before Timing Demo ===")
    logging.info("This demo tests if an assignment happens only when the target is not yet complete.")

    # 1. Create repositories
    concept_repo, inference_repo = create_repositories()

    # 2. Initialize and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        max_cycles=15,
    )

    # 3. Run the orchestrator
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

    logging.info(f"=== @before Timing Demo Complete - Log saved to {log_filename} ===")
    print(f"\n{'='*80}")
    print("PROGRAM COMPLETED")
    print(f"{'='*80}")