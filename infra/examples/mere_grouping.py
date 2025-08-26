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

# Import core components
try:
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body


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

def run_grouping_sequence() -> BaseStates:

    concept_to_infer, value_concepts, function_concept, context_concepts = _build_demo_concepts()

    inference = Inference(
        "grouping",
        concept_to_infer,
        function_concept,
        value_concepts,
        context_concepts=context_concepts
    )
    
    agent = AgentFrame("demo", working_interpretation=_build_demo_working_interpretation(), body=Body())

    agent.configure(inference, "grouping")

    states = inference.execute()

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

def run_complex_grouping_sequence() -> BaseStates:
    """Runs the more complex grouping demonstration."""

    concept_to_infer, value_concepts, function_concept, context_concepts = _build_complex_demo_concepts()

    inference = Inference(
        "grouping",
        concept_to_infer,
        function_concept,
        value_concepts,
        context_concepts=context_concepts
    )
    
    agent = AgentFrame("demo", working_interpretation=_build_complex_demo_working_interpretation(), body=Body())
    agent.configure(inference, "grouping")
    states = inference.execute()

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
