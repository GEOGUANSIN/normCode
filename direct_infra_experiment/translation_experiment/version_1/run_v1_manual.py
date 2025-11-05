import uuid
import logging
import os
import sys
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
    here = Path(__file__).parent
    project_root = here.parent.parent.parent
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
normcode_file = Path(__file__).parent / "v1_manual.ncd"
with open(normcode_file, "r") as f:
    Normcode_draft = f.read()


def create_repositories():
    """Creates concept and inference repositories for a mock conditional loop scenario."""

    # --- Prompt File Paths ---
    prompt_dir = Path(__file__).parent / "prompts"
    normtext_prompt_path = f"%{{prompt}}({(prompt_dir / 'normtext_prompt').resolve()})"
    initialization_prompt_path = f"%{{prompt}}({(prompt_dir / 'initialization_prompt').resolve()})"
    completion_check_prompt_path = f"%{{prompt}}({(prompt_dir / 'completion_check_prompt').resolve()})"
    decomposition_step_prompt_path = f"%{{prompt}}({(prompt_dir / 'decomposition_step_prompt').resolve()})"
    concept_identification_prompt_path = f"%{{prompt}}({(prompt_dir / 'concept_identification_prompt').resolve()})"
    question_inquiry_prompt_path = f"%{{prompt}}({(prompt_dir / 'question_inquiry_prompt').resolve()})"
    operator_selection_prompt_path = f"%{{prompt}}({(prompt_dir / 'operator_selection_prompt').resolve()})"
    children_concept_creation_prompt_path = f"%{{prompt}}({(prompt_dir / 'children_concept_creation_prompt').resolve()})"
    normtext_distribution_prompt_path = f"%{{prompt}}({(prompt_dir / 'normtext_distribution_prompt').resolve()})"
    normcode_draft_update_prompt_path = f"%{{prompt}}({(prompt_dir / 'normcode_draft_update_prompt').resolve()})"

    concept_entries = [
        # Final Concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normcode draft}",
            type="{}",
            description="The final, processed normcode draft.",
            axis_name="value",
            is_final_concept=True,
        ),

        # Inferred Concepts
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normtext}<$={1}>",
            type="{}",
            description="Initial text from a prompt.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normcode draft}<$={1}>",
            type="{}",
            axis_name="value",
            description="An initialized normcode draft.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[all {normcode draft}]",
            type="[]",
            axis_name="value",
            description="A collection of normcode drafts.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normcode draft}<$={2}>",
            type="{}",
            axis_name="value",
            description="The destination draft if it is complete.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="<current normcode draft is complete>",
            type="<>",
            description="Judgement result, true if current item is complete.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normcode draft}<$={3}>",
            type="{}",
            axis_name="value",
            description="Result of decomposition.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{prompt}",
            type="{}",
            description="A prompt for an LLM.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normtext}?",
            type="{}",
            description="A query for normtext.",
            is_ground_concept=True,
            reference_data=[normtext_prompt_path],
            reference_axis_names=["value"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{initialization prompt}",
            type="{}",
            description="A prompt for initialization.",
            is_ground_concept=True,
            reference_data=[initialization_prompt_path],
            reference_axis_names=["value"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{completion check prompt}",
            type="{}",
            description="A prompt for completion check.",
            is_ground_concept=True,
            reference_data=[completion_check_prompt_path],
            reference_axis_names=["value"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{decomposition step prompt}",
            type="{}",
            description="A prompt for decomposition.",
            is_ground_concept=True,
            reference_data=[decomposition_step_prompt_path],
            reference_axis_names=["value"],
        ),

        # --- New Decomposition Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[{concept to decomposed} and {remaining normtext}]",
            type="[]",
            description="The concept to be decomposed and the remaining normtext.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[{question} and {question type}]",
            type="[]",
            description="The inquiry question and its type for decomposition.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{functional concept}",
            type="{}",
            description="The functional concept for the new inference.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{children concepts}",
            type="{}",
            description="The children concepts for the new inference.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{new inference}",
            type="{}",
            description="The newly generated inference.",
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normcode draft}<$={4}>",
            type="{}",
            axis_name="value",
            description="The updated normcode draft after incorporating the new inference.",
        ),

        # --- New Prompt Concepts ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{concept identification prompt}",
            type="{}",
            description="A prompt for concept identification.",
            is_ground_concept=True,
            reference_data=[concept_identification_prompt_path],
            reference_axis_names=["value"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{question inquiry prompt}",
            type="{}",
            description="A prompt for question inquiry.",
            is_ground_concept=True,
            reference_data=[question_inquiry_prompt_path],
            reference_axis_names=["value"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{operator selection prompt}",
            type="{}",
            description="A prompt for operator selection.",
            is_ground_concept=True,
            reference_data=[operator_selection_prompt_path],
            reference_axis_names=["value"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{children concept creation prompt}",
            type="{}",
            description="A prompt for children concept creation.",
            is_ground_concept=True,
            reference_data=[children_concept_creation_prompt_path],
            reference_axis_names=["value"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normtext distribution prompt}",
            type="{}",
            description="A prompt for normtext distribution.",
            is_ground_concept=True,
            reference_data=[normtext_distribution_prompt_path],
            reference_axis_names=["value"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{normcode draft update prompt}",
            type="{}",
            description="A prompt for updating the normcode draft.",
            is_ground_concept=True,
            reference_data=[normcode_draft_update_prompt_path],
            reference_axis_names=["value"],
        ),


        # Functional Concepts
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name=':>:({prompt}<:{normtext}>)',
            type=":>:",
            description="Imperative function to get initial text.",
            is_ground_concept=True,
            is_invariant=True,
            # Mocking the prompt to return a simple string
            reference_data=[':>:({prompt}<:{normtext}>)'],
            reference_axis_names=["_none_axis"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(direct)}({prompt}<$({initialization prompt})%>: initialize normcode draft)",
            type="::",
            description="Direct imperative to initialize a draft from text.",
            is_ground_concept=True,
            is_invariant=True,
            # Mocking the initialization to be an int conversion
            reference_data=["::{%(direct)}({prompt}<$({initialization prompt})%>: initialize normcode draft)"],
            reference_axis_names=["_none_axis"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="&across({normcode draft})",
            type="&across",
            description="Grouping function.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="*every([all {normcode draft}])",
            type="*every",
            description="The quantifier for the main loop.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({normcode draft}<$={#}>)",
            type="$.",
            description="Assignment to the loop's result collector.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>",
            type="<{}>",
            description="Judgement function to check if a draft is complete.",
            is_ground_concept=True,
            is_invariant=True,
            # Mocking the completion check to be a simple numerical comparison
            reference_data=["::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>"],
            reference_axis_names=["_none_axis"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.([all {normcode draft}]*1)",
            type="$.",
            description="Assignment to loop item.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({normcode draft})",
            type="$.",
            description="Final assignment.",
            is_ground_concept=True,
        ),

        # --- New Functional Concepts for Decomposition ---
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="$.({normcode draft}<$={4}>)",
            type="$.",
            description="Assignment to the decomposed draft.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>",
            type="::",
            description="Imperative to identify the concept to decompose.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>"],
            reference_axis_names=["_none_axis"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>",
            type="::",
            description="Imperative to formulate a question about the concept.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>"],
            reference_axis_names=["_none_axis"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>",
            type="::",
            description="Imperative to select a NormCode operator.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>"],
            reference_axis_names=["_none_axis"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>",
            type="::",
            description="Imperative to create child concepts for the new inference.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>"],
            reference_axis_names=["_none_axis"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>",
            type="::",
            description="Imperative to distribute normtext among child concepts.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>"],
            reference_axis_names=["_none_axis"],
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>",
            type="::",
            description="Imperative to update the normcode draft with the new inference.",
            is_ground_concept=True,
            is_invariant=True,
            reference_data=["::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>"],
            reference_axis_names=["_none_axis"],
        ),

        # Timing Concepts
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@if(<current normcode draft is complete>)",
            type="@if",
            description="Conditional execution if draft is complete.",
            is_ground_concept=True,
        ),
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="@if!(<current normcode draft is complete>)",
            type="@if!",
            description="Conditional execution if draft is not complete.",
            is_ground_concept=True,
        ),

        # Loop Item Concept
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="[all {normcode draft}]*1",
            type="[]",
            description="The current item from the draft sequence in a loop.",
        ),
    ]
    concept_repo = ConceptRepo(concept_entries)

    # --- Inference Entries ---
    inference_entries = [
        # Final Assignment
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{normcode draft}'),
            function_concept=concept_repo.get_concept('$.({normcode draft})'),
            value_concepts=[concept_repo.get_concept('[all {normcode draft}]')],
            flow_info={'flow_index': '1'},
            working_interpretation={"syntax": {"marker": ".", "assign_source": "[all {normcode draft}]", "assign_destination": "{normcode draft}"}}
        ),
        # Initial Imperative for normtext
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_input',
            concept_to_infer=concept_repo.get_concept('{normtext}<$={1}>'),
            function_concept=concept_repo.get_concept(':>:({prompt}<:{normtext}>)'),
            value_concepts=[concept_repo.get_concept('{normtext}?')],
            flow_info={'flow_index': '1.1'},
            working_interpretation={
                "prompt_location": "normtext_prompt",
                "value_order": {
                    "{normtext}?": 1,
                }
            }
        ),

        # Direct Imperative for initial normcode draft
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_direct',
            concept_to_infer=concept_repo.get_concept('{normcode draft}<$={1}>'),
            function_concept=concept_repo.get_concept('::{%(direct)}({prompt}<$({initialization prompt})%>: initialize normcode draft)'),
            value_concepts=[
                concept_repo.get_concept('{normtext}<$={1}>'),
                concept_repo.get_concept('{initialization prompt}')
            ],
            flow_info={'flow_index': '1.2'},
            working_interpretation={
                "prompt_location": "initialization_prompt",
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{initialization prompt}": 0,
                    "{normtext}<$={1}>": 1,
                }
            }
        ),

        # Grouping
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=concept_repo.get_concept('[all {normcode draft}]'),
            function_concept=concept_repo.get_concept('&across({normcode draft})'),
            value_concepts=[concept_repo.get_concept('{normcode draft}<$={1}>')],
            flow_info={'flow_index': '1.3'},
            working_interpretation={"syntax": {"marker": "across", "by_axis_concepts": "{normcode draft}<$={1}>"}}
        ),

        # Quantifying (Main Loop)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('[all {normcode draft}]'),
            function_concept=concept_repo.get_concept('*every([all {normcode draft}])'),
            value_concepts=[concept_repo.get_concept('[all {normcode draft}]')],
            context_concepts=[concept_repo.get_concept('[all {normcode draft}]*1')],
            flow_info={'flow_index': '1.4'},
            working_interpretation={
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 1,
                    "LoopBaseConcept": "[all {normcode draft}]",
                    "CurrentLoopBaseConcept": "[all {normcode draft}]*1",
                    "group_base": "normcode draft",
                    "InLoopConcept": {},
                    "ConceptToInfer": ["[all {normcode draft}]"]
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
            concept_to_infer=concept_repo.get_concept('*every([all {normcode draft}])'),
            function_concept=concept_repo.get_concept('$.({normcode draft}<$={#}>)'),
            value_concepts=[
                concept_repo.get_concept('[all {normcode draft}]'),
                concept_repo.get_concept('{normcode draft}<$={2}>'),
                concept_repo.get_concept('{normcode draft}<$={3}>'),
                concept_repo.get_concept('<current normcode draft is complete>'),
                ],
            flow_info={'flow_index': '1.4.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": ["{normcode draft}<$={3}>", "{normcode draft}<$={2}>"],
                    "assign_destination": "*every([all {normcode draft}])"
                }
            }
        ),


        # Judgement
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='judgement_direct',
            concept_to_infer=concept_repo.get_concept('<current normcode draft is complete>'),
            function_concept=concept_repo.get_concept('::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>'),
            value_concepts=[
                concept_repo.get_concept('[all {normcode draft}]*1'),
                concept_repo.get_concept('{completion check prompt}')
            ],
            flow_info={'flow_index': '1.4.1.1'},
            working_interpretation={
                "prompt_location": "completion_check_prompt",
                "with_thinking": True,
                "condition": "True",
                "value_order": {
                    "{completion check prompt}": 0,
                    "[all {normcode draft}]*1": 1,
                }
            }
        ),

        # Conditional Assignment
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{normcode draft}<$={2}>'),
            function_concept=concept_repo.get_concept('$.([all {normcode draft}]*1)'),
            value_concepts=[
                concept_repo.get_concept('[all {normcode draft}]*1'),
                concept_repo.get_concept('<current normcode draft is complete>')
            ],
            flow_info={'flow_index': '1.4.1.2'},
            working_interpretation={
                "syntax": {
                    "marker": ".", "assign_source": "[all {normcode draft}]*1", "assign_destination": "{normcode draft}<$={2}>",
                }
            }
        ),

        # Timing for Conditional Assignment
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('$.([all {normcode draft}]*1)'),
            function_concept=concept_repo.get_concept('@if(<current normcode draft is complete>)'),
            value_concepts=[concept_repo.get_concept('<current normcode draft is complete>')],
            flow_info={'flow_index': '1.4.1.2.1'},
            working_interpretation={
                "syntax": {
                    "marker": "if",
                    "condition": "<current normcode draft is complete>"
                }
            }
        ),

        # Assignment for decomposition result
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=concept_repo.get_concept('{normcode draft}<$={3}>'),
            function_concept=concept_repo.get_concept('$.({normcode draft}<$={4}>)'),
            value_concepts=[
                concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
                concept_repo.get_concept('[{question} and {question type}]'),
                concept_repo.get_concept('{functional concept}'),
                concept_repo.get_concept('{children concepts}'),
                concept_repo.get_concept('{new inference}'),
                concept_repo.get_concept('{normcode draft}<$={4}>'),
            ],
            flow_info={'flow_index': '1.4.1.3'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "{normcode draft}<$={4}>",
                    "assign_destination": "{normcode draft}<$={3}>",
                }
            }
        ),

        # Timing for decomposition block
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=concept_repo.get_concept('$.({normcode draft}<$={4}>)'),
            function_concept=concept_repo.get_concept('@if!(<current normcode draft is complete>)'),
            value_concepts=[concept_repo.get_concept('<current normcode draft is complete>')],
            flow_info={'flow_index': '1.4.1.3.1'},
            working_interpretation={
                "syntax": {
                    "marker": "if!",
                    "condition": "<current normcode draft is complete>"
                }
            }
        ),

        # Imperative for concept identification
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_direct',
            concept_to_infer=concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
            function_concept=concept_repo.get_concept('::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>'),
            value_concepts=[
                concept_repo.get_concept('[all {normcode draft}]*1'),
                concept_repo.get_concept('{concept identification prompt}')
            ],
            flow_info={'flow_index': '1.4.1.3.2'},
            working_interpretation={
                "is_relation_output": True,
                "with_thinking": True,
                "value_order": {
                    "{concept identification prompt}": 0,
                    "[all {normcode draft}]*1": 1,
                }
            }
        ),

        # Imperative for question inquiry
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_direct',
            concept_to_infer=concept_repo.get_concept('[{question} and {question type}]'),
            function_concept=concept_repo.get_concept('::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>'),
            value_concepts=[
                concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
                concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
                concept_repo.get_concept('{question inquiry prompt}')
            ],
            flow_info={'flow_index': '1.4.1.3.3'},
            working_interpretation={
                "is_relation_output": True,
                "with_thinking": True,
                "value_order": {
                    "{question inquiry prompt}": 0,
                    "[{concept to decomposed} and {remaining normtext}]_1": 1,
                    "[{concept to decomposed} and {remaining normtext}]_2": 2,
                },
                "value_selectors": {
                    "[{concept to decomposed} and {remaining normtext}]_1": {
                        "source_concept": "[{concept to decomposed} and {remaining normtext}]",
                        "index": 0,
                        "key": "concept to decomposed"
                    },
                    "[{concept to decomposed} and {remaining normtext}]_2": {
                        "source_concept": "[{concept to decomposed} and {remaining normtext}]",
                        "index": 0,
                        "key": "remaining normtext"
                    }
                }
            }
        ),

        # Imperative for operator selection
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_direct',
            concept_to_infer=concept_repo.get_concept('{functional concept}'),
            function_concept=concept_repo.get_concept('::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>'),
            value_concepts=[
                concept_repo.get_concept('[{question} and {question type}]'),
                concept_repo.get_concept('[{question} and {question type}]'),
                concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
                concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
                concept_repo.get_concept('{operator selection prompt}')
            ],
            flow_info={'flow_index': '1.4.1.3.4'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{operator selection prompt}": 0,
                    "[{question} and {question type}]_1": 1,
                    "[{concept to decomposed} and {remaining normtext}]_1": 2,
                    "[{question} and {question type}]_2": 3,
                    "[{concept to decomposed} and {remaining normtext}]_2": 4,
                },
                "value_selectors": {
                    "[{question} and {question type}]_1": {
                        "source_concept": "[{question} and {question type}]", "index": 0, "key": "question"
                    },
                    "[{question} and {question type}]_2": {
                        "source_concept": "[{question} and {question type}]", "index": 0, "key": "question type"
                    },
                    "[{concept to decomposed} and {remaining normtext}]_1": {
                        "source_concept": "[{concept to decomposed} and {remaining normtext}]", "index": 0, "key": "concept to decomposed"
                    },
                    "[{concept to decomposed} and {remaining normtext}]_2": {
                        "source_concept": "[{concept to decomposed} and {remaining normtext}]", "index": 0, "key": "remaining normtext"
                    }
                }
            }
        ),

        # Imperative for children concept creation
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_direct',
            concept_to_infer=concept_repo.get_concept('{children concepts}'),
            function_concept=concept_repo.get_concept('::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>'),
            value_concepts=[
                concept_repo.get_concept('{functional concept}'),
                concept_repo.get_concept('[{question} and {question type}]'),
                concept_repo.get_concept('[{question} and {question type}]'),
                concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
                concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
                concept_repo.get_concept('{children concept creation prompt}'),
            ],
            flow_info={'flow_index': '1.4.1.3.5'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{children concept creation prompt}": 0,
                    "[{concept to decomposed} and {remaining normtext}]_1": 1,
                    "[{concept to decomposed} and {remaining normtext}]_2": 2,
                    "[{question} and {question type}]_1": 3,
                    "[{question} and {question type}]_2": 4,
                    "{functional concept}": 5,
                },
                "value_selectors": {
                    "[{question} and {question type}]_1": {
                        "source_concept": "[{question} and {question type}]", "index": 0, "key": "question"
                    },
                    "[{question} and {question type}]_2": {
                        "source_concept": "[{question} and {question type}]", "index": 0, "key": "question type"
                    },
                    "[{concept to decomposed} and {remaining normtext}]_1": {
                        "source_concept": "[{concept to decomposed} and {remaining normtext}]", "index": 0, "key": "concept to decomposed"
                    },
                    "[{concept to decomposed} and {remaining normtext}]_2": {
                        "source_concept": "[{concept to decomposed} and {remaining normtext}]", "index": 0, "key": "remaining normtext"
                    }
                }
            }
        ),

        # Imperative for normtext distribution
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_direct',
            concept_to_infer=concept_repo.get_concept('{new inference}'),
            function_concept=concept_repo.get_concept('::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>'),
            value_concepts=[
                concept_repo.get_concept('{functional concept}'),
                concept_repo.get_concept('{children concepts}'),
                concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
                concept_repo.get_concept('[{concept to decomposed} and {remaining normtext}]'),
                concept_repo.get_concept('{normtext distribution prompt}'),
            ],
            flow_info={'flow_index': '1.4.1.3.6'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{normtext distribution prompt}": 0,
                    "[{concept to decomposed} and {remaining normtext}]_1": 1,
                    "{functional concept}": 2,
                    "{children concepts}": 3,
                    "[{concept to decomposed} and {remaining normtext}]_2": 4,
                },
                "value_selectors": {
                    "[{concept to decomposed} and {remaining normtext}]_1": {
                        "source_concept": "[{concept to decomposed} and {remaining normtext}]",
                        "index": 0,
                        "key": "concept to decomposed"
                    },
                    "[{concept to decomposed} and {remaining normtext}]_2": {
                        "source_concept": "[{concept to decomposed} and {remaining normtext}]",
                        "index": 0,
                        "key": "remaining normtext"
                    }
                }
            }
        ),

        # Imperative for normcode draft update
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative_direct',
            concept_to_infer=concept_repo.get_concept('{normcode draft}<$={4}>'),
            function_concept=concept_repo.get_concept('::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>'),
            value_concepts=[
                concept_repo.get_concept('[all {normcode draft}]*1'),
                concept_repo.get_concept('{new inference}'),
                concept_repo.get_concept('{normcode draft update prompt}'),
            ],
            flow_info={'flow_index': '1.4.1.3.7'},
            working_interpretation={
                "is_relation_output": False,
                "with_thinking": True,
                "value_order": {
                    "{normcode draft update prompt}": 0,
                    "[all {normcode draft}]*1": 1,
                    "{new inference}": 2,
                }
            }
        ),

        # Grouping inside loop
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='grouping',
            concept_to_infer=concept_repo.get_concept('[all {normcode draft}]'),
            function_concept=concept_repo.get_concept('&across({normcode draft})'),
            value_concepts=[
                concept_repo.get_concept('{normcode draft}<$={2}>'),
                concept_repo.get_concept('{normcode draft}<$={3}>')
            ],
            flow_info={'flow_index': '1.4.1.4'},
            working_interpretation={"syntax": {"marker": "across", "by_axis_concepts": ["{normcode draft}<$={2}>", "{normcode draft}<$={3}>"]}}
        ),
    ]
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo


if __name__ == "__main__":
    # Setup file logging
    log_filename = setup_orchestrator_logging(__file__)
    logging.info("=== Starting Imperative Direct Draft Demo ===")
    logging.info("This demo tests a conditional loop with direct imperatives.")

    # 1. Create repositories
    concept_repo, inference_repo = create_repositories()

    # 2. Initialize and run the orchestrator

    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        max_cycles=30,
        body=Body("qwen-plus"),
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

    logging.info(f"=== Imperative Direct Draft Demo Complete - Log saved to {log_filename} ===")
    print(f"\n{'='*80}")
    print("PROGRAM COMPLETED")
    print(f"{'='*80}")
