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
    sys.path.insert(0, str(here.parent.parent.parent))
    from infra import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo, Orchestrator, Blackboard, Body
    from infra._loggers.utils import setup_orchestrator_logging

# Import the result validator and random number generator
from result_validator import ResultValidator
from random_number_generator import RandomNumberGenerator, quick_generate, generate_test_suite



# --- Normcode for this example ---

Normcode_new_with_appending = """
{new number pair} | 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>] | 1.1. assigning

        <= $.({remainder}) 
        
        <- {digit sum} | 1.1.2. imperative
            <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
            <- {sum}?<:{3}>
            <- {carry-over number}*1<:{2}> 
            <- [all {unit place value} of numbers]<:{1}> | 1.1.2.4. grouping
                <= &across({unit place value}:{number pair}*1)
                <- {unit place value} | 1.1.2.4.2. quantifying
                    <= *every({number pair}*1)%:[{number}]@(2) | 1.1.2.4.2.1. assigning
                        <= $.({single unit place value})
                        <- {single unit place value} | 1.1.2.4.2.1.2. imperative
                            <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)
                            <- {unit place digit}?<:{2}>
                            <- {number pair}*1*2
                    <- {number pair}*1

        <- {number pair}<$={1}> | 1.1.3. assigning
            <= $+({number pair to append}:{number pair})%:[{number pair}] | 1.1.3.1. timing
                <= @if!(<all number is 0>) | 1.1.3.1.1. timing
                    <= @if(<carry-over number is 0>)

            <- {number pair to append}<$={1}> | 1.1.3.2. quantifying
                <= *every({number pair}*1)%:[{number}]@(3) | 1.1.3.2.1. assigning
                    <= $.({number with last digit removed}) 
                    <- {number with last digit removed} | 1.1.3.2.1.2. imperative
                        <= ::(output 0 if {1}<$({number})%_> is less than 10, otherwise remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>) 
                        <- {unit place digit}?<:{2}> 
                        <- {number pair}*1*3<:{1}>
                <- {number pair}*1

            <- <all number is 0> | 1.1.3.3. judgement
                <= :%(True):<{1}<$({number})%_> is 0> | 1.1.3.3.1. timing
                    <= @after({number pair to append}<$={1}>)
                <- {number pair to append}<$={1}><:{1}>

            <- <carry-over number is 0> | 1.1.3.4. judgement
                <= :%(True):<{1}<$({carry-over number})%_> is 0> | 1.1.3.4.1. timing
                    <= @after({number pair to append}<$={1}>)
                <- {carry-over number}*1<:{1}>

        <- {carry-over number}*1 | 1.1.4. grouping
            <= &across({carry-over number}*1:{carry-over number}*1<--<!_>>)
            <- {carry-over number}*1 | 1.1.4.2. imperative
                <= ::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10) | 1.1.4.2.1. timing
                    <= @after({digit sum})
                <- {quotient}?<:{1}>
                <- {digit sum}<:{2}>

        <- {remainder} | 1.1.5. imperative
            <= ::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10) | 1.1.5.1. timing
                <= @after({digit sum})
            <- {remainder}?<:{1}>
            <- {digit sum}<:{2}>

    <- {number pair}<$={1}> |ref. %(number pair)=[%(number)=[123, 98]]
"""

# --- Data Definitions ---

def create_appending_repositories_new(number_1: str = "123", number_2: str = "98" ):
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
            reference_data=[["%(" + number_1 + ")", "%(" + number_2 + ")"]],
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
            concept_name="{carry-over number}?",
            type="{}",
            axis_name="carry-over number query",
            description="A query for the carry-over number from a sum.",
            reference_data=["1 if the number is larger than 10"],
            reference_axis_names=["carry-over number"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{quotient}?",
            type="{}",
            axis_name="quotient",
            description="A query for the quotient of a division.",
            reference_data=["the quotient when dividing by 10"],
            reference_axis_names=["quotient"],
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{remainder}?",
            type="{}",
            axis_name="remainder explanation",
            description="A query for the remainder of a division.",
            reference_data=["the remainder when dividing by 10"],
            reference_axis_names=["remainder explanation"],
            is_ground_concept=True,
        ),
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
        # Concepts for Digit Summation
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{digit sum}",
            type="{}",
            axis_name="digit sum",
            description="The sum of digits at the current position, including carry-over.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{remainder}",
            type="{}",
            axis_name="remainder",
            description="The remainder of a digit sum divided by 10.",
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
            description="The carry-over value from a digit sum.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{carry-over number}*1",
            type="{}",
            axis_name="current carry-over number",
            description="The carry-over value for the current digit position.",
            reference_data=["%(0)"],
            reference_axis_names=["carry-over number"],
            is_ground_concept=True,
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
            concept_name="<all number is 0>",
            type="<>",
            axis_name="all number is 0",
            description="A boolean concept indicating if all numbers are zero.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="<carry-over number is 0>",
            type="<>",
            axis_name="carry-over number is 0",
            description="A boolean concept indicating if the carry-over number is zero.",
        ),

        # --- Function Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]",
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
            concept_name="$.({digit sum})",
            type="$.",
            description="Pass-through function for the digit sum.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({remainder})",
            type="$.",
            description="Pass-through function for the remainder.",
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
            concept_name="$.({single unit place value})",
            type="$.",
            description="Pass-through function for a single unit place value.",
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
            reference_axis_names=["get unit place digit"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)",
            type="::({})",
            description="Adds the digits at the current unit place and the carry-over.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)"],
            reference_axis_names=["sum"],
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
            concept_name="&across({carry-over number}*1:{carry-over number}*1<--<!_>>)",
            type="&across",
            description="Groups carry-over number with by_axis_concepts as inferring concepts excluding base concept variants.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(get the {1}?<$({carry-over number})%_> of {2}<$({digit sum})%_>)",
            type="::({})",
            description="Gets the carry-over number from a digit sum.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["get carry-over"],
            reference_axis_names=["get carry-over"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10)",
            type="::({})",
            description="Finds the quotient of a digit sum divided by 10.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["find quotient by dividing by 10"],
            reference_axis_names=["find quotient"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10)",
            type="::({})",
            description="Gets the remainder of a digit sum divided by 10.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["get remainder by dividing by 10"],
            reference_axis_names=["get remainder"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@after({digit sum})",
            type="@after",
            description="Timing condition to execute after digit sum is calculated.",
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
            concept_name=":%(True):<{1}<$({number})%_> is 0>",
            type="<{}>",
            description="Judgement function to check if a number is zero.",
            is_ground_concept=True,
            reference_data='::<{1}<$({number})%_> is 0>',
            reference_axis_names=["is_0"],
            is_invariant=True
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name=":%(True):<{1}<$({carry-over number})%_> is 0>",
            type="<{}>",
            description="Judgement function to check if a carry-over number is zero.",
            is_ground_concept=True,
            reference_data='::<{1}<$({carry-over number})%_> is 0>',
            reference_axis_names=["carry_over_is_0"],
            is_invariant=True
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@if!(<all number is 0>)",
            type="@if!",
            description="Timing condition to check if not all numbers are zero.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@if(<carry-over number is 0>)",
            type="@if",
            description="Timing condition to check if carry-over number is zero.",
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
            function_concept=concept_repo.get_concept('*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]'),
            value_concepts=[concept_repo.get_concept('{number pair}')],
            context_concepts=[concept_repo.get_concept('{number pair}*1'), concept_repo.get_concept('{carry-over number}*1')],
            flow_info={'flow_index': '1'},
            working_interpretation={
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 1,
                    "LoopBaseConcept": "{number pair}",
                    "CurrentLoopBaseConcept": "{number pair}*1",
                    "group_base": "number pair",
                    "InLoopConcept": {
                        "{carry-over number}*1": 1,
                    },
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
            concept_to_infer=concept_repo.get_concept('*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]'),
            function_concept=concept_repo.get_concept('$.({remainder})'),
            value_concepts=[concept_repo.get_concept('{remainder}')],
            flow_info={'flow_index': '1.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "{remainder}",
                    "assign_destination": "*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]"
                }
            },
        ),
        # 1.1.2. Imperative for {digit sum}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{digit sum}'),
            function_concept=concept_repo.get_concept('::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)'),
            value_concepts=[
                concept_repo.get_concept('[all {unit place value} of numbers]'),
                concept_repo.get_concept('{carry-over number}*1'),
                concept_repo.get_concept('{sum}?'),
            ],
            flow_info={'flow_index': '1.1.2'},
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
        # 1.1.2.4 Grouping for [all {unit place value} of numbers]
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=concept_repo.get_concept('[all {unit place value} of numbers]'),
            function_concept=concept_repo.get_concept('&across({unit place value}:{number pair}*1)'),
            value_concepts=[
                concept_repo.get_concept('{unit place value}'),
            ],
            context_concepts=[concept_repo.get_concept('{number pair}*1')],
            flow_info={'flow_index': '1.1.2.4'},
            working_interpretation={
                "syntax": {
                    "marker": "across",
                    "by_axis_concepts": "{number pair}*1"

                }
            }
        ),
        # 1.1.2.4.2 Quantifying for {unit place value}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('{unit place value}'),
            function_concept=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(2)'),
            value_concepts=[concept_repo.get_concept('{number pair}*1')],
            context_concepts=[concept_repo.get_concept('{number pair}*1*2')],
            flow_info={'flow_index': '1.1.2.4.2'},
            working_interpretation={
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 2,
                    "LoopBaseConcept": "{number pair}*1",
                    "CurrentLoopBaseConcept": "{number pair}*1*2",
                    "group_base": "number",
                    "InLoopConcept": {},
                    "ConceptToInfer": ["{unit place value}"],
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_with_support_reference_only=True
        ),
        # 1.1.2.4.2.1 Assigning for inner loop
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('*every({number pair}*1)%:[{number}]@(2)'),
            function_concept=concept_repo.get_concept('$.({single unit place value})'),
            value_concepts=[concept_repo.get_concept('{single unit place value}')],
            flow_info={'flow_index': '1.1.2.4.2.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "{single unit place value}",
                    "assign_destination": "*every({number pair}*1)%:[{number}]@(2)"
                }
            },
        ),
        # 1.1.2.4.2.1.2 Imperative for {single unit place value}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{single unit place value}'),
            function_concept=concept_repo.get_concept('::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)'),
            value_concepts=[
                concept_repo.get_concept('{number pair}*1*2'),
                concept_repo.get_concept('{unit place digit}?'),
            ],
            flow_info={'flow_index': '1.1.2.4.2.1.2'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{number pair}*1*2": 1,
                    "{unit place digit}?": 2
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
            function_concept=concept_repo.get_concept('@if!(<all number is 0>)'),
            value_concepts=[concept_repo.get_concept('<all number is 0>')],
            flow_info={'flow_index': '1.1.3.1'},
            working_interpretation={
                "syntax": {
                    "marker": "if!",
                    "condition": "<all number is 0>"
                }
            }
        ),
        # 1.1.3.1.1. Nested timing for carry-over check
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('@if!(<all number is 0>)'),
            function_concept=concept_repo.get_concept('@if(<carry-over number is 0>)'),
            value_concepts=[concept_repo.get_concept('<carry-over number is 0>')],
            flow_info={'flow_index': '1.1.3.1.1'},
            working_interpretation={
                "syntax": {
                    "marker": "if",
                    "condition": "<carry-over number is 0>"
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
            concept_to_infer=concept_repo.get_concept('<all number is 0>'),
            function_concept=concept_repo.get_concept(':%(True):<{1}<$({number})%_> is 0>'),
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
                "condition": "True"
            }
        ),
        # 1.1.3.3.1. Timing for judgement
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept(':%(True):<{1}<$({number})%_> is 0>'),
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
        # 1.1.3.4. Judgement for carry-over number is zero
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='judgement',
            concept_to_infer=concept_repo.get_concept('<carry-over number is 0>'),
            function_concept=concept_repo.get_concept(':%(True):<{1}<$({carry-over number})%_> is 0>'),
            value_concepts=[
                concept_repo.get_concept('{carry-over number}*1'),
            ],
            flow_info={'flow_index': '1.1.3.4'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{carry-over number}*1": 1
                },
                "condition": "True"
            }
        ),
        # 1.1.3.4.1. Timing for carry-over judgement
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept(':%(True):<{1}<$({carry-over number})%_> is 0>'),
            function_concept=concept_repo.get_concept('@after({number pair to append}<$={1}>)'),
            value_concepts=[concept_repo.get_concept('{number pair to append}')],
            flow_info={'flow_index': '1.1.3.4.1'},
            working_interpretation={
                "syntax": {
                    "marker": "after",
                    "condition": "{number pair to append}"
                }
            }
        ),
        # 1.1.4. Grouping for {carry-over number}*1
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=concept_repo.get_concept('{carry-over number}*1'),
            function_concept=concept_repo.get_concept('&across({carry-over number}*1:{carry-over number}*1<--<!_>>)'),
            value_concepts=[
                concept_repo.get_concept('{carry-over number}*1'),
            ],
            context_concepts=[
                concept_repo.get_concept('::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10)'),
                concept_repo.get_concept('{digit sum}'),
                concept_repo.get_concept('{quotient}?')
            ],
            flow_info={'flow_index': '1.1.4'},
            working_interpretation={
                "syntax": {
                    "marker": "across",
                    "by_axis_concepts": [
                        "::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10)",
                        "{digit sum}",
                        "{quotient}?"
                    ],
                    "protect_axes": ["carry-over number"]
                }
            }
        ),
        # 1.1.4.2. Imperative for {carry-over number}*1
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{carry-over number}*1'),
            function_concept=concept_repo.get_concept('::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10)'),
            value_concepts=[
                concept_repo.get_concept('{digit sum}'),
                concept_repo.get_concept('{quotient}?'),
            ],
            flow_info={'flow_index': '1.1.4.2'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{quotient}?": 1,
                    "{digit sum}": 2
                }
            },
        ),
        # 1.1.4.2.1. Timing for imperative
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10)'),
            function_concept=concept_repo.get_concept('@after({digit sum})'),
            value_concepts=[concept_repo.get_concept('{digit sum}')],
            flow_info={'flow_index': '1.1.4.2.1'},
            working_interpretation={
                "syntax": {
                    "marker": "after",
                    "condition": "{digit sum}"
                }
            }
        ),
        # 1.1.5. Imperative for {remainder}
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=concept_repo.get_concept('{remainder}'),
            function_concept=concept_repo.get_concept(
                '::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10)'),
            value_concepts=[
                concept_repo.get_concept('{digit sum}'),
                concept_repo.get_concept('{remainder}?'),
            ],
            flow_info={'flow_index': '1.1.5'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{remainder}?": 1,
                    "{digit sum}": 2
                }
            },
        ),
        # 1.1.5.1. Timing for imperative
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept(
                '::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10)'),
            function_concept=concept_repo.get_concept('@after({digit sum})'),
            value_concepts=[concept_repo.get_concept('{digit sum}')],
            flow_info={'flow_index': '1.1.5.1'},
            working_interpretation={
                "syntax": {
                    "marker": "after",
                    "condition": "{digit sum}"
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


def validate_orchestrator_results(final_concepts, input_numbers):
    """
    Validate the results from the orchestrator using the ResultValidator.
    
    Args:
        final_concepts: List of final concept entries from the orchestrator
        input_numbers: Tuple of input numbers (number_1, number_2)
        
    Returns:
        ValidationResult object with detailed analysis
    """
    validator = ResultValidator()
    
    # Find the {new number pair} concept
    new_number_pair_concept = None
    for concept_entry in final_concepts:
        if concept_entry and concept_entry.concept_name == '{new number pair}':
            new_number_pair_concept = concept_entry
            break
    
    if not new_number_pair_concept:
        logging.error("Could not find '{new number pair}' concept in final results")
        return None
    
    if not new_number_pair_concept.concept.reference:
        logging.error("No reference found for '{new number pair}' concept")
        return None
    
    # Extract the data
    ref = new_number_pair_concept.concept.reference
    data_tensor = ref.tensor
    axis_names = ref.axes
    shape = ref.shape
    
    logging.info("=== VALIDATING ORCHESTRATOR RESULTS ===")
    logging.info(f"Input numbers: {input_numbers}")
    logging.info(f"Data tensor: {data_tensor}")
    logging.info(f"Axis names: {axis_names}")
    logging.info(f"Shape: {shape}")
    
    # Perform validation
    validation_result = validator.validate_final_concept(
        concept_name='{new number pair}',
        data_tensor=data_tensor,
        axis_names=axis_names,
        shape=shape,
        input_numbers=input_numbers
    )
    
    # Print validation report
    validator.print_validation_report(validation_result)
    
    # Log validation results
    logging.info(f"Validation result: {'VALID' if validation_result.is_valid else 'INVALID'}")
    if validation_result.errors:
        for error in validation_result.errors:
            logging.error(f"Validation error: {error}")
    if validation_result.warnings:
        for warning in validation_result.warnings:
            logging.warning(f"Validation warning: {warning}")
    
    return validation_result


def run_with_random_numbers(min_length: int = 1, 
                           max_length: int = 5, 
                           seed: Optional[int] = None,
                           include_edge_cases: bool = True,
                           include_carry_cases: bool = True,
                           test_count: int = 10):
    """
    Run the orchestrator with random number inputs and validate results.
    
    Args:
        min_length: Minimum number of digits (default: 1)
        max_length: Maximum number of digits (default: 5)
        seed: Optional seed for reproducible generation
        include_edge_cases: Whether to include edge cases (default: True)
        include_carry_cases: Whether to include carry cases (default: True)
        test_count: Number of random test cases to generate (default: 10)
    """
    print(f"\n{'='*80}")
    print("RUNNING ORCHESTRATOR WITH RANDOM NUMBER INPUTS")
    print(f"{'='*80}")
    print(f"Configuration:")
    print(f"  - Min/Max length: {min_length}/{max_length}")
    print(f"  - Seed: {seed}")
    print(f"  - Include edge cases: {include_edge_cases}")
    print(f"  - Include carry cases: {include_carry_cases}")
    print(f"  - Test count: {test_count}")
    
    # Generate test cases
    test_cases = generate_test_suite(
        count=test_count,
        include_edge_cases=include_edge_cases,
        include_carry_cases=include_carry_cases,
        min_length=min_length,
        max_length=max_length,
        seed=seed
    )
    
    print(f"\nGenerated {len(test_cases)} test cases")
    
    # Run tests
    results = []
    for i, (number_1, number_2) in enumerate(test_cases):
        print(f"\n{'-'*60}")
        print(f"TEST CASE {i+1}/{len(test_cases)}: {number_1} + {number_2}")
        print(f"{'-'*60}")
        
        try:
            # Create repositories with current numbers
            concept_repo, inference_repo = create_appending_repositories_new(
                number_1=number_1,
                number_2=number_2
            )
            
            # Initialize and run the orchestrator
            orchestrator = Orchestrator(
                concept_repo=concept_repo,
                inference_repo=inference_repo,
                max_cycles=70,
            )
            
            # Run the orchestrator
            final_concepts = orchestrator.run()
            
            # Validate the results
            validation_result = validate_orchestrator_results(final_concepts, (number_1, number_2))
            
            # Store results
            result_summary = {
                'input': (number_1, number_2),
                'expected_sum': int(number_1) + int(number_2),
                'validation_passed': validation_result.is_valid if validation_result else False,
                'errors': validation_result.errors if validation_result else [],
                'warnings': validation_result.warnings if validation_result else [],
                'accuracy': validation_result.digit_analysis.get('summary', {}).get('accuracy_percentage', 0) if validation_result else 0
            }
            results.append(result_summary)
            
            # Quick status
            status = "✓ PASS" if result_summary['validation_passed'] else "✗ FAIL"
            print(f"\n{status} - Accuracy: {result_summary['accuracy']:.1f}%")
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            result_summary = {
                'input': (number_1, number_2),
                'expected_sum': int(number_1) + int(number_2),
                'validation_passed': False,
                'errors': [f"Execution error: {str(e)}"],
                'warnings': [],
                'accuracy': 0
            }
            results.append(result_summary)
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['validation_passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print(f"\nFailed test cases:")
        for i, result in enumerate(results):
            if not result['validation_passed']:
                input_str = f"{result['input'][0]} + {result['input'][1]}"
                print(f"  {i+1}. {input_str} (Expected: {result['expected_sum']})")
                for error in result['errors']:
                    print(f"     Error: {error}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the number pair addition orchestrator')
    parser.add_argument('--random', action='store_true', 
                       help='Run with random number inputs instead of fixed values')
    parser.add_argument('--min-length', type=int, default=1,
                       help='Minimum number of digits for random generation (default: 1)')
    parser.add_argument('--max-length', type=int, default=5,
                       help='Maximum number of digits for random generation (default: 5)')
    parser.add_argument('--test-count', type=int, default=10,
                       help='Number of random test cases to run (default: 10)')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed for reproducible generation (default: None)')
    parser.add_argument('--no-edge-cases', action='store_true',
                       help='Exclude edge cases from random testing')
    parser.add_argument('--no-carry-cases', action='store_true',
                       help='Exclude carry cases from random testing')
    parser.add_argument('--number1', type=str, default="12",
                       help='First number for fixed input mode (default: "12")')
    parser.add_argument('--number2', type=str, default="92",
                       help='Second number for fixed input mode (default: "92")')
    
    args = parser.parse_args()
    
    if args.random:
        # Run with random numbers
        print("Running in RANDOM MODE")
        results = run_with_random_numbers(
            min_length=args.min_length,
            max_length=args.max_length,
            seed=args.seed,
            include_edge_cases=not args.no_edge_cases,
            include_carry_cases=not args.no_carry_cases,
            test_count=args.test_count
        )
    else:
        # Run with fixed numbers (original behavior)
        print("Running in FIXED MODE")
        
        # Setup file logging
        log_filename = setup_orchestrator_logging(__file__)
        logging.info("=== Starting Orchestrator Demo ===")

        # 1. Create repositories
        number_1, number_2 = quick_generate(min_length=1, max_length=2, seed=25)
        logging.info(f"Generated numbers: {number_1} + {number_2}")

        # number_1 = args.number1
        # number_2 = args.number2
        concept_repo, inference_repo = create_appending_repositories_new(
            number_1=number_1,
            number_2=number_2
        )

        # 2. Initialize and run the orchestrator
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            max_cycles=45,
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

        # 5. Validate the results
        print("\n" + "="*60)
        print("VALIDATING RESULTS")
        print("="*60)
        validation_result = validate_orchestrator_results(final_concepts, (number_1, number_2))
        
        if validation_result and validation_result.is_valid:
            print("\n🎉 All validations passed!")
        elif validation_result:
            print(f"\n❌ Validation failed with {len(validation_result.errors)} errors")
        else:
            print("\n⚠️  Validation could not be completed")

        logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===")
    
    print(f"\n{'='*80}")
    print("PROGRAM COMPLETED")
    print(f"{'='*80}") 