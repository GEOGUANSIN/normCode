import os
import sys
import logging
from typing import Any, Dict, List, Optional, Callable
from types import SimpleNamespace
from dataclasses import dataclass, field
from string import Template

# Ensure this directory is importable regardless of where the script is run from
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from .._core import Inference, register_inference_sequence, setup_logging
from .._core import Concept
from .._core import Reference, cross_product, cross_action, element_action
from copy import copy
from .._syntax import Grouper
from .._states import States

from .._agent._steps.grouping import (
    iwi,
    ir,
    gr,
    or_step,
    owi,
)

# --- State Models ---

# --- Grouping Step Implementations ---

def input_working_interpretation(
    inference: Inference, 
    states: States, 
    working_interpretation: Optional[Dict[str, Any]] = None
) -> States:
    """Initialize states with syntax info and placeholder records."""
    if working_interpretation:
        states.syntax.marker = working_interpretation.get("syntax", {}).get("marker")

    # Seed lists with empty records for each step
    for step in ["GR", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logging.debug(f"IWI completed. Syntax marker: {states.syntax.marker}")
    return states

def input_references(inference: Inference, states: States) -> States:
    """Populate references and concept info into the state from the inference instance."""
    if inference.function_concept:
        states.function.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(id=inference.function_concept.id, name=inference.function_concept.name, type=inference.function_concept.type, context=inference.function_concept.context, axis_name=inference.function_concept.axis_name),
                reference=inference.function_concept.reference.copy() if inference.function_concept.reference else None
            )
        )
    
    for vc in inference.value_concepts or []:
        states.values.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(id=vc.id, name=vc.name, type=vc.type, context=vc.context, axis_name=vc.axis_name),
                reference=vc.reference.copy() if vc.reference else None
            )
        )

    for cc in inference.context_concepts or []:
        states.context.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(id=cc.id, name=cc.name, type=cc.type, context=cc.context, axis_name=cc.axis_name),
                reference=cc.reference.copy() if cc.reference else None
            )
        )
    
    states.set_current_step("IR")
    logging.debug(f"IR completed. Loaded {len(states.values)} value and {len(states.context)} context concepts.")
    return states

def grouping_references(states: States) -> States:
    """Perform the core grouping logic."""
    context_refs = [r.reference for r in states.context if r.reference]
    value_refs = [r.reference for r in states.values if r.reference]
    value_concept_names = [c.concept.name for c in states.values if c.concept]

    by_axes = [ref.axes for ref in context_refs]

    grouper = Grouper()
    result_ref = None

    if states.syntax.marker == "in":
        logging.debug(f"Performing 'and_in' grouping with by_axes: {by_axes}")
        result_ref = grouper.and_in(
            value_refs,
            value_concept_names,
            by_axes=by_axes,
        )
    elif states.syntax.marker == "across":
        logging.debug(f"Performing 'or_across' grouping with by_axes: {by_axes}")
        result_ref = grouper.or_across(
            value_refs,
            by_axes=by_axes,
        )
    else:
        logging.warning(f"No valid grouping marker found ('{states.syntax.marker}'). Skipping grouping.")
        # Create an empty reference to avoid errors downstream
        result_ref = Reference(axes=["result"], shape=(0,))

    if result_ref:
        states.set_reference("inference", "GR", result_ref)

    states.set_current_step("GR")
    logging.debug("GR completed.")
    return states

def output_reference(states: States) -> States:
    """Finalize the output reference."""
    gr_ref = states.get_reference("inference", "GR")
    if gr_ref:
        states.set_reference("inference", "OR", gr_ref)
    states.set_current_step("OR")
    logging.debug("OR completed.")
    return states

def output_working_interpretation(states: States) -> States:
    """No-op finalization for demo."""
    states.set_current_step("OWI")
    logging.debug("OWI completed.")
    return states

# --- Logging ---
def log_states_progress(states: States, step_name: str, step_filter: Optional[str] = None):
    logger = logging.getLogger(__name__)
    logger.info(f"\n--- States after {step_name} (Filtered by: {step_filter or 'None'}) ---")
    logger.info(f"Current Step: {states.sequence_state.current_step}")
    
    def _log_record_list(label: str, record_list: List[ReferenceRecordLite]):
        logger.info(f"{label}:")
        filtered_records = [item for item in record_list if step_filter is None or item.step_name == step_filter]
        if not filtered_records:
            logger.info("  (Empty or no matching records for filter)")
            return
        for item in filtered_records:
            logger.info(f"  Step Name: {item.step_name}")
            if item.concept:
                logger.info(f"    Concept ID: {item.concept.id}, Name: {item.concept.name}, Type: {item.concept.type}, Context: {item.concept.context}, Axis: {item.concept.axis_name}")
            if item.reference and isinstance(item.reference, Reference):
                logger.info(f"    Reference Axes: {item.reference.axes}")
                logger.info(f"    Reference Shape: {item.reference.shape}")
                logger.info(f"    Reference Tensor: {item.reference.tensor}")

    _log_record_list("Function", states.function)
    _log_record_list("Values", states.values)
    _log_record_list("Context", states.context)
    _log_record_list("Inference", states.inference)
    logger.info("-----------------------------------")


# --- Grouping Sequence Runner ---

@register_inference_sequence("grouping_v2")
def grouping_v2(self: Inference, input_data: Optional[Dict[str, Any]] = None) -> States:
    """New grouping sequence runner."""
    states = States()
    working_interpretation = (input_data or {}).get("working_interpretation")

    # IWI
    states = iwi.input_working_interpretation(
        self, states, working_interpretation=working_interpretation
    )
    log_states_progress(states, "IWI", "IWI")
    # IR
    states = ir.input_references(self, states)
    log_states_progress(states, "IR", "IR")
    # GR
    states = gr.grouping_references(states)
    log_states_progress(states, "GR", "GR")
    # OR
    states = or_step.output_reference(states)
    log_states_progress(states, "OR", "OR")
    # OWI
    states = owi.output_working_interpretation(states)
    log_states_progress(states, "OWI", "OWI")

    return states

# --- Demo Setup ---

def _build_demo_concepts() -> tuple[Concept, List[Concept], Concept, List[Concept]]:
    """Builds concepts for a grouping demo."""
    # Value Concepts
    ref_animals = Reference(axes=["animal_id"], shape=(3,))
    for i, v in enumerate(["cat", "dog", "fish"]):
        ref_animals.set(f"%({v})", animal_id=i)
    concept_animals = Concept("{animals}", "animals", "animal_id", ref_animals)

    ref_colors = Reference(axes=["color_id"], shape=(3,))
    for i, v in enumerate(["black", "brown", "gold"]):
        ref_colors.set(f"%({v})", color_id=i)
    concept_colors = Concept("{colors}", "colors", "color_id", ref_colors)

    # Context Concept
    ref_context = Reference(axes=["animal_id", "color_id"], shape=(3, 3))
    # This context links specific animals to colors
    context_data = [
        [1, 1, 0], # cat -> black, cat -> brown
        [0, 1, 0], # dog -> brown
        [0, 0, 1]  # fish -> gold
    ]
    for i in range(3):
        for j in range(3):
            if context_data[i][j] == 1:
                ref_context.set(1, animal_id=i, color_id=j)

    concept_context = Concept("{animal_colors}", "animal_colors", "animal_colors", ref_context)
    
    # Concept to Infer (placeholder)
    concept_to_infer = Concept("{grouped_result}", "grouped_result", "grouped_result")

    # Function Concept (placeholder)
    function_concept = Concept("{grouping_function}", "grouping_function", "grouping_function")
    
    return concept_to_infer, [concept_animals, concept_colors], function_concept, [concept_context]

def _build_demo_working_interpretation() -> Dict[str, Any]:
    return {
        "syntax": {
            "marker": "in" 
        }
    }

# --- Main Execution ---

def run_grouping_sequence() -> States:
    setup_logging(logging.DEBUG)

    concept_to_infer, value_concepts, function_concept, context_concepts = _build_demo_concepts()

    inference = Inference(
        "grouping_v2",
        concept_to_infer,
        value_concepts,
        function_concept,
        context_concepts=context_concepts
    )
    
    states = inference.execute(input_data={
        "working_interpretation": _build_demo_working_interpretation()
    })

    final_ref = states.get_reference("inference", "OR")
    if isinstance(final_ref, Reference):
        logger = logging.getLogger(__name__)
        logger.info("--- Final Output (OR) ---")
        logger.info(f"Axes: {final_ref.axes}")
        logger.info(f"Shape: {final_ref.shape}")
        # Log tensor content more clearly
        tensor_content = final_ref.get_tensor(ignore_skip=True)
        logger.info(f"Tensor (without skips):")
        for item in tensor_content:
            logger.info(f"  - {item}")
        
        # Also print for clarity
        print("\n--- Final Output (OR) ---")
        print(f"Axes: {final_ref.axes}")
        print(f"Shape: {final_ref.shape}")
        print("Tensor (without skips):")
        for item in tensor_content:
            print(f"  - {item}")
    
    return states


# --- Demo Setup for Complex Example ---

def _build_complex_demo_concepts() -> tuple[Concept, List[Concept], Concept, List[Concept]]:
    """Builds concepts for a more complex grouping demo with student data."""
    logger = logging.getLogger(__name__)
    logger.info("Building complex demo concepts for student data grouping.")

    # --- Value Concepts ---
    # 1. Grades
    ref_grades = Reference(axes=["student_id", "subject_id"], shape=(2, 3))
    grades_data = [[90, 85, 92], [88, 91, 86]]  # Alice, Bob
    for i in range(2):
        for j in range(3):
            ref_grades.set(f"%(grade:{grades_data[i][j]})", student_id=i, subject_id=j)
    concept_grades = Concept("{grades}", "grades", "grades_axis", ref_grades)

    # 2. Attendance
    ref_attendance = Reference(axes=["student_id", "subject_id"], shape=(2, 3))
    attendance_data = [[95, 98, 92], [100, 90, 95]] # %
    for i in range(2):
        for j in range(3):
            ref_attendance.set(f"%(attd:{attendance_data[i][j]}%)", student_id=i, subject_id=j)
    concept_attendance = Concept("{attendance}", "attendance", "attendance_axis", ref_attendance)

    # --- Context Concepts ---
    # 1. Subject Names (used as context to group by)
    ref_subjects = Reference(axes=["subject_id"], shape=(3,))
    for i, v in enumerate(["Math", "Science", "History"]):
        ref_subjects.set(f"%({v})", subject_id=i)
    concept_subjects = Concept("{subjects}", "subjects", "subject_id", ref_subjects)

    # Concept to Infer
    concept_to_infer = Concept("{student_performance}", "student_performance", "student_performance_axis")
    
    # Function Concept (placeholder)
    function_concept = Concept("{grouping_function}", "grouping_function", "grouping_function")
    
    # We want to group grades and attendance by student. So `student_id` is the preserved axis.
    # The axis we group over and collapse is `subject_id`. So this becomes the `by_axis`.
    # Therefore, `concept_subjects` should be the context concept for grouping.
    
    return (
        concept_to_infer, 
        [concept_grades, concept_attendance], # Value concepts to be grouped
        function_concept, 
        [concept_subjects] # Context concept to define the grouping axis (`by_axes`)
    )

def _build_complex_demo_working_interpretation() -> Dict[str, Any]:
    return {
        "syntax": {
            "marker": "in" 
        }
    }


# --- Main Execution for Complex Example ---

def run_complex_grouping_sequence() -> States:
    """Runs the more complex grouping demonstration."""
    setup_logging(logging.DEBUG)

    concept_to_infer, value_concepts, function_concept, context_concepts = _build_complex_demo_concepts()

    inference = Inference(
        "grouping_v2",
        concept_to_infer,
        value_concepts,
        function_concept,
        context_concepts=context_concepts
    )
    
    states = inference.execute(input_data={
        "working_interpretation": _build_complex_demo_working_interpretation()
    })

    final_ref = states.get_reference("inference", "OR")
    if isinstance(final_ref, Reference):
        logger = logging.getLogger(__name__)
        logger.info("--- Complex Demo Final Output (OR) ---")
        logger.info(f"Axes: {final_ref.axes}")
        logger.info(f"Shape: {final_ref.shape}")
        tensor_content = final_ref.get_tensor(ignore_skip=True)
        logger.info(f"Tensor (without skips):")
        for i, item in enumerate(tensor_content):
            logger.info(f"  Item {i}:")
            # item is a list of dictionaries
            if isinstance(item, list):
                for record in item:
                    logger.info(f"    - {record}")
            else:
                 logger.info(f"    - {item}")
        
        print("\n--- Complex Demo Final Output (OR) ---")
        print(f"Axes: {final_ref.axes}")
        print(f"Shape: {final_ref.shape}")
        print("Tensor (without skips):")
        for i, item in enumerate(tensor_content):
            print(f"  Student {i}:")
            if isinstance(item, list):
                for record in item:
                    print(f"    - {record}")
            else:
                print(f"    - {item}")

    return states


if __name__ == "__main__":
    print("--- Running Simple Demo ---")
    run_grouping_sequence()
    print("\n\n--- Running Complex Demo ---")
    run_complex_grouping_sequence()
