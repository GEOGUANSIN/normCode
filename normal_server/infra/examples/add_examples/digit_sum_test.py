import uuid
import logging
import os
import sys

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
    sys.path.insert(0, str(here.parent.parent.parent))
    from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Blackboard, Body
    from infra._loggers.utils import setup_orchestrator_logging

# --- Normcode for this example ---
Normcode_digit_sum = """
{digit sum} | 1. imperative
    <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
    <- {sum}?<:{3}>
    <- {carry-over number}*1<:{2}> | 1.3.1. assigning
        <- $.({carry-over number})
        <- {carry-over number}
    <- [all {unit place value} of numbers]<:{1}> | 1.4. grouping
        <= &across({unit place value}:{number pair}*1)
        <- {unit place value} | 1.4.2. quantifying
            <= *every({number pair}*1)%:[{number}]@(1) | 1.4.2.1. assigning
                <= $.({single unit place value})
                <- {single unit place value} | 1.4.2.1.2. imperative
                    <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)
                    <- {unit place digit}?<:{2}>
                    <- {number pair}*1*1
            <- {number pair}*1
"""

# --- Data Definitions ---
def create_digit_sum_repositories(number_1: str = "123", number_2: str = "98"):
    """Creates concept and inference repositories for the digit sum scenario."""
    # --- Concept Entries ---
    concept_entries = [
        # --- Ground & Final Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{digit sum}",
            type="{}",
            axis_name="digit sum",
            description="The final sum of digits.",
            is_final_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}*1",
            type="{}",
            axis_name="current number pair",
            description="The specific pair of numbers being processed.",
            reference_data=[["%(" + number_1 + ")", "%(" + number_2 + ")"]],
            reference_axis_names=["number pair", "number"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{unit place digit}?",
            type="{}",
            axis_name="unit place digit",
            context="the digit extracted from the current position",
            description="The extracted digit from the current position",
            reference_data=['1 digit counting from the right'],
            reference_axis_names=["unit place digit"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{sum}?",
            type="{}",
            axis_name="sum",
            description="The resulting sum from the digit summation operation.",
            context="the resulting sum from the digit summation operation",
            reference_data=['the addition result of numbers'],
            reference_axis_names=["sum"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{carry-over number}",
            type="{}",
            axis_name="carry-over number",
            description="The carry-over value for the next digit position.",
            reference_data=["%(0)"],
            reference_axis_names=["carry-over number"],
            is_ground_concept=True,
        ),

        # --- Intermediate Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number}",
            type="{}",
            axis_name="number",
            description="An individual number, part of a pair.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}*1*1",
            type="{}",
            axis_name="current number from pair",
            description="The specific number being processed in the current iteration of the loop.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{carry-over number}*1",
            type="{}",
            axis_name="current carry-over number",
            description="The carry-over value for the current digit position.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[all {unit place value} of numbers]",
            type="[]",
            axis_name="all unit place value of numbers",
            description="A collection of all unit place values from the numbers in the current pair.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{unit place value}",
            type="{}",
            axis_name="unit place value",
            description="The digit at the current unit place for a single number.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{single unit place value}",
            type="{}",
            axis_name="single unit place value",
            description="The digit at the current unit place for a single number, processed in a loop.",
        ),

        # --- Function Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every({number pair}*1)%:[{number}]@(1)",
            type="*every",
            description="Loop quantifier: iterates over each number in a pair.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({single unit place value})",
            type="$.",
            description="Pass-through function for a single unit place value.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({carry-over number})",
            type="$.",
            description="Pass-through function for carry-over number.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="&across({unit place value}:{number pair}*1)",
            type="&across",
            description="Groups unit place values from numbers.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)",
            type="::({})",
            description="Gets the unit place digit from a number.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["get unit place digit"],
            reference_axis_names=["get"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(sum {1}<$({number})%_> and {2}<$({carry-over number})%_> to get {3}?<$({sum})%_>)",
            type="::({})",
            description="Adds the digits at the current unit place and the carry-over.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::(sum {1}<$({number})%_> and {2}<$({carry-over number})%_> to get {3}?<$({sum})%_>)"],
            reference_axis_names=["sum"],
        ),
    ]
    concept_repo = ConceptRepo(concept_entries)

    # --- Inference Entries ---
    inference_entries = [
        # 1. Imperative for {digit sum}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{digit sum}'),
            function_concept=concept_repo.get_concept('::(sum {1}<$({number})%_> and {2}<$({carry-over number})%_> to get {3}?<$({sum})%_>)'),
            value_concepts=[
                concept_repo.get_concept('[all {unit place value} of numbers]'),
                concept_repo.get_concept('{carry-over number}*1'),
                concept_repo.get_concept('{sum}?'),
            ],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "[all {unit place value} of numbers]": 1,
                    "{carry-over number}*1": 2,
                    "{sum}?": 3
                },
            },
        ),
        # Add an assigning step to initialize {carry-over number}*1
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{carry-over number}*1'),
            function_concept=concept_repo.get_concept('$.({carry-over number})'),
            value_concepts=[concept_repo.get_concept('{carry-over number}')],
            flow_info={'flow_index': '1.3.1'},
             working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "{carry-over number}",
                    "assign_destination": "{carry-over number}*1"
                }
            },
        ),
        # 1.1 Grouping for [all {unit place value} of numbers]
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=concept_repo.get_concept('[all {unit place value} of numbers]'),
            function_concept=concept_repo.get_concept('&across({unit place value}:{number pair}*1)'),
            value_concepts=[
                concept_repo.get_concept('{unit place value}'),
            ],
            context_concepts=[concept_repo.get_concept('{number pair}*1')],
            flow_info={'flow_index': '1.4'},
            working_interpretation={
                "syntax": {
                    "marker": "across",
                    "by_axis_concepts": "{number pair}*1"

                }
            }
        ),
        # 1.1.1 Quantifying for {unit place value}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('{unit place value}'),
            function_concept=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(1)'),
            value_concepts=[concept_repo.get_concept('{number pair}*1')],
            context_concepts=[concept_repo.get_concept('{number pair}*1*1')],
            flow_info={'flow_index': '1.4.2'},
            working_interpretation={
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 1,
                    "LoopBaseConcept": "{number pair}*1",
                    "CurrentLoopBaseConcept": "{number pair}*1*1",
                    "group_base": "number",
                    "InLoopConcept": {},
                    "ConceptToInfer": ["{unit place value}"],
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_with_support_reference_only=True
        ),
        # 1.1.1.1 Assigning for inner loop
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(1)'),
            function_concept=concept_repo.get_concept('$.({single unit place value})'),
            value_concepts=[concept_repo.get_concept('{single unit place value}')],
            flow_info={'flow_index': '1.4.2.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "{single unit place value}",
                    "assign_destination": "*every({number pair}*1)%:[{number}]@(1)"
                }
            },
        ),
        # 1.1.1.1.1 Imperative for {single unit place value}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{single unit place value}'),
            function_concept=concept_repo.get_concept('::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)'),
            value_concepts=[
                concept_repo.get_concept('{number pair}*1*1'),
                concept_repo.get_concept('{unit place digit}?'),
            ],
            flow_info={'flow_index': '1.4.2.1.2'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{number pair}*1*1": 1,
                    "{unit place digit}?": 2
                }
            },
        ),
    ]
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo


if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Digit Sum Demo ===")

    # 1. Create repositories
    number_1 = "12563"
    number_2 = "9232"
    concept_repo, inference_repo = create_digit_sum_repositories(
        number_1=number_1,
        number_2=number_2
    )

    # 2. Initialize and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        max_cycles=20,
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

    logging.info(f"=== Digit Sum Demo Complete - Log saved to {log_filename} ===")
