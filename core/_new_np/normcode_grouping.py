import logging
from typing import List, Optional, Any, Dict, Union
from string import Template
from _concept import Concept
from copy import copy
from _reference import Reference, cross_product, element_action
from _methods._demo import strip_element_wrapper, wrap_element_wrapper
from _methods._grouping_demo import Grouper, formal_actuator_perception

# Configure logging
def setup_logging(level=logging.INFO):
    """Setup logging configuration for NormCodeGroup"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger('NormCodeGroup')
    logger.info(f"NormCodeGroup logging initialized at level: {logging.getLevelName(level)}")
    return logger

# Create logger instance
logger = setup_logging()

def set_log_level(level):
    """Set the logging level for NormCodeGroup"""
    if level.upper() == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif level.upper() == 'INFO':
        logger.setLevel(logging.INFO)
    elif level.upper() == 'WARNING':
        logger.setLevel(logging.WARNING)
    elif level.upper() == 'ERROR':
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)
    logger.info(f"Log level set to: {level.upper()}")


def log_concept(concept):
    logger.debug("\n" + "-"*60 + "\n")
    logger.debug(f"Concept: {concept.name}")
    if concept.context is not None:
        logger.debug(f"  Context: {concept.context}")
    if concept.reference is not None:
        logger.debug(f"  Reference: {concept.reference.tensor}")
        logger.debug(f"  Reference axes: {concept.reference.axes}")
        logger.debug(f"  Reference shape: {concept.reference.shape}")
    logger.debug("\n" + "-"*60 + "\n")


# Example usage and demonstration
def demonstrate_normcode_group():
    """
    Demonstrate the NormCodeGroup class with examples similar to slice_with_normcode.py
    """
    logger.info("Starting NormCodeGroup demonstration")
    
    # Create a group instance
    grouper = Grouper()
    logger.info("Created NormCodeGroup instance")
    
    logger.info("Demonstrating AND IN Pattern")
    print("1. AND IN Pattern: [{old expression} and {new expression} in all {old expression}]")
    print("   |ref. [%[%[%{old expression}:(tech), %{new expression}[:(techie)]], %[%{old expression}:(couch), %{new expression}[:(couchie)]]]]")
    print("   <= &in({old expression};{new expression})%:[{old expression}]")
    print("   <- {old expression}")
    print("       |ref. [%O[0]=%(tech), %O[1]=%(couch)]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    print("   <- {new expression}")
    print("       |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    
    # Create sample references
    old_ref = Reference(
        axes=['O'],
        shape=(2,),
        initial_value=0
    )
    old_ref.tensor = ['%(tech)', '%(couch)']
    
    new_ref = Reference(
        axes=['O', 'N'],
        shape=(2, 1),
        initial_value=0
    )
    new_ref.tensor = [['%(techie)'], ['%(couchie)']]
    
    print(f"\nReference old shape: {old_ref.shape}")
    print(f"Reference old axes: {old_ref.axes}")
    print(f"Reference old data: {old_ref.tensor}")
    
    print(f"\nReference new shape: {new_ref.shape}")
    print(f"Reference new axes: {new_ref.axes}")
    print(f"Reference new data: {new_ref.tensor}")
    
    # Create template for processing
    template = Template("Transform old expression (being '${input1}') into some new expression (like being '${input2}').")
    
    result_and_in = grouper.and_in([old_ref, new_ref], ['{old expression}', '{new expression}'], ['O'])
    print(f"\nResult shape: {result_and_in.shape}")
    print(f"Result axes: {result_and_in.axes}")
    print(f"Result data: {result_and_in.tensor}")

    expected_result = "[[{'{old expression}': '%(tech)', '{new expression}': ['%(techie)']}, {'{old expression}': '%(couch)', '{new expression}': ['%(couchie)']}]]"
    print(f"expected: {expected_result}")
    
    # Apply template processing
    result_and_in_templated = grouper.and_in([old_ref, new_ref], ['{old expression}', '{new expression}'], ['O'], template)
    print(f"\nTemplated result: {result_and_in_templated.tensor}")
    logger.info("AND IN Pattern demonstration completed")
    
    print("\n" + "="*60 + "\n")
    
    print("2. OR ACROSS Pattern: [{old expression} or {new expression} across all {old expression}]")
    print("   |ref. [[%(tech), %(techie), %(couch), %(couchie)]]")
    print("   <= &across({old expression};{new expression})%:[{old expression}]")
    print("   <- {old expression}")
    print("       |ref. [%O[0]=%(tech), %O[1]=%(couch)]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    print("   <- {new expression}")
    print("       |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    
    # Create a different template for OR ACROSS pattern that only uses input1
    or_across_template = Template("Transform expressions: ${input1}")
    result_or_across = grouper.or_across([old_ref, new_ref], ['O'])
    print(f"\nResult shape: {result_or_across.shape}")
    print(f"Result axes: {result_or_across.axes}")
    print(f"Result data: {result_or_across.tensor}")

    expected_result = "[['%(tech)', '%(techie)', '%(couch)', '%(couchie)']]"
    print(f"expected: {expected_result}")
    
    # Apply template processing
    result_or_across_templated = grouper.or_across([old_ref, new_ref], ['O'], or_across_template)
    print(f"\nTemplated result: {result_or_across_templated.tensor}")
    logger.info("OR ACROSS Pattern demonstration completed")
    
    print("\n" + "="*60 + "\n")
    
    print("3. AND ONLY Pattern: [{old expression} and {new expression}]")
    print("   |ref. [%O[0]=[%[%{old expression}:(tech), %{new expression}:(techie)]], %O[1]=[%[%{old expression}:(couch), %{new expression}:(couchie)]]]")
    print("   <= &and({old expression};{new expression})")
    print("   <- {old expression}")
    print("       |ref. [%O[0]=%(tech), %O[1]=%(couch)]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    print("   <- {new expression}")
    print("       |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    
    result_and_only = grouper.and_in([old_ref, new_ref], ['{old expression}', '{new expression}'])
    print(f"\nResult shape: {result_and_only.shape}")
    print(f"Result axes: {result_and_only.axes}")
    print(f"Result data: {result_and_only.tensor}")

    expected_result = "[{'{old expression}': '%(tech)', '{new expression}': ['%(techie)']}, {'{old expression}': '%(couch)', '{new expression}': ['%(couchie)']}]"
    print(f"expected: {expected_result}")
    
    # Apply template processing
    result_and_only_templated = grouper.and_in([old_ref, new_ref], ['{old expression}', '{new expression}'], template=template)
    print(f"\nTemplated result: {result_and_only_templated.tensor}")
    logger.info("AND ONLY Pattern demonstration completed")
    
    print("\n" + "="*60 + "\n")
    
    print("4. OR ONLY Pattern: [{old expression} or {new expression}]")
    print("   |ref. [%O[0]=%[%(tech), %(techie)], %O[1]=%[%(couch), %(couchie)]]")
    print("   <= &across({old expression};{new expression})")
    print("   <- {old expression}")
    print("       |ref. [%O[0]=%(tech), %O[1]=%(couch)]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    print("   <- {new expression}")
    print("       |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    
    # Create a different template for OR ONLY pattern
    or_template = Template("Identify the longer expression (being '$output') in old expression or new expression (being '${input1}').")
    
    result_or_only = grouper.or_across([old_ref, new_ref])
    print(f"\nResult shape: {result_or_only.shape}")
    print(f"Result axes: {result_or_only.axes}")
    print(f"Result data: {result_or_only.tensor}")

    expected_result = "[['%(tech)', '%(techie)'], ['%(couch)', '%(couchie)']]"
    print(f"expected: {expected_result}")
    
    # Apply template processing
    result_or_only_templated = grouper.or_across([old_ref, new_ref], template=or_template)
    print(f"\nTemplated result: {result_or_only_templated.tensor}")
    logger.info("OR ONLY Pattern demonstration completed")
    
    print("\n" + "="*60 + "\n")
    
    print("5. SIMPLE OR ONLY Pattern: [{A} or {B}]")
    print("   |ref. [%D[0]=%[%(a1), %(b1), %(b2)]], %D[1]=%[%(a2), %(b1), %(b2)]]")
    print("   <= &or(A; B)")
    print("   <- A |ref. [%D[0]=[%A[0]=%(a1)], %D[1]=[%A[1]=%(a2)]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%(b1), %B[1]=%(b2)]], [%D[1]=[%B[0]=%(b1), %B[1]=%(b2)]]]")
    
    # Create references for simple OR ONLY pattern
    A_ref = Reference(
        axes=['D', 'A'],
        shape=(2, 1),
        initial_value=0
    )
    A_ref.tensor = [['%(a1)'], ['%(a2)']]
    
    B_ref = Reference(
        axes=['D', 'B'],
        shape=(2, 2),
        initial_value=0
    )
    B_ref.tensor = [['%(b1)', '%(b2)'], ['%(b1)', '%(b2)']]
    
    print(f"\nReference A shape: {A_ref.shape}")
    print(f"Reference A axes: {A_ref.axes}")
    print(f"Reference A data: {A_ref.tensor}")
    
    print(f"\nReference B shape: {B_ref.shape}")
    print(f"Reference B axes: {B_ref.axes}")
    print(f"Reference B data: {B_ref.tensor}")
    
    result_simple_or_only = grouper.or_across([A_ref, B_ref])
    print(f"\nResult shape: {result_simple_or_only.shape}")
    print(f"Result axes: {result_simple_or_only.axes}")
    print(f"Result data: {result_simple_or_only.tensor}")
    
    expected_result = "[['%(a1)', '%(b1)', '%(b2)'], ['%(a2)', '%(b1)', '%(b2)']]"
    print(f"expected: {expected_result}")
    
    # Create template for simple patterns
    simple_template = Template("Combine elements: ${input1}")
    result_simple_or_only_templated = grouper.or_across([A_ref, B_ref], template=simple_template)
    print(f"\nTemplated result: {result_simple_or_only_templated.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("6. SIMPLE AND ONLY Pattern: [{A} and {B}]")
    print("   |ref. [%D[0]=[%[%{A}:(a1), %{B}[:(b1), :(b2)]]], %D[1]=[%[%{A}:(a2), %{B}[:(b1), :(b2)]]]]")
    print("   <= &and(A; B)")
    print("   <- A |ref. [%D[0]=[%A[0]=%(a1)]], [%D[1]=[%A[1]=%(a2)]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%(b1), %B[1]=%(b2)]], [%D[1]=[%B[0]=%(b1), %B[1]=%(b2)]]]")
    
    result_simple_and_only = grouper.and_in([A_ref, B_ref], ['{A}', '{B}'])
    print(f"\nResult shape: {result_simple_and_only.shape}")
    print(f"Result axes: {result_simple_and_only.axes}")
    print(f"Result data: {result_simple_and_only.tensor}")

    expected_result = "[{'{A}': ['%(a1)'], '{B}': ['%(b1)', '%(b2)']}, {'{A}': ['%(b1)', '%(b2)']}]"
    print(f"expected: {expected_result}")
    
    # Apply template processing
    simple_and_template = Template("A is '${input1}' and B is '${input2}'")
    result_simple_and_only_templated = grouper.and_in([A_ref, B_ref], ['{A}', '{B}'], template=simple_and_template)
    print(f"\nTemplated result: {result_simple_and_only_templated.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("7. SIMPLE OR ACROSS Pattern: [{A} or {B} across all {A}]")
    print("   |ref. [[%(a1), %(b1), %(b2), %(a2), %(b1), %(b2)]]")
    print("   <= &across(A; B)%:[{A}]")
    print("   <- A |ref. [%D[0]=[%A[0]=%(a1)]], [%D[1]=[%A[1]=%(a2)]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%(b1), %B[1]=%(b2)]], [%D[1]=[%B[0]=%(b1), %B[1]=%(b2)]]]")
    
    result_simple_or_across = grouper.or_across([A_ref, B_ref], ['D'])
    print(f"\nResult shape: {result_simple_or_across.shape}")
    print(f"Result axes: {result_simple_or_across.axes}")
    print(f"Result data: {result_simple_or_across.tensor}")

    expected_result = "[['%(a1)', '%(b1)', '%(b2)', '%(a2)', '%(b1)', '%(b2)']]"
    print(f"expected: {expected_result}")
    
    # Apply template processing
    result_simple_or_across_templated = grouper.or_across([A_ref, B_ref], ['D'], simple_template)
    print(f"\nTemplated result: {result_simple_or_across_templated.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("8. SIMPLE AND IN Pattern: [{A} and {B} in all {A}]")
    print("   |ref. [%[%{A}[:(a1)], %{B}[:(b1), :(b2)]], %[%{A}[:(a2)], %{B}[:(b1), :(b2)]]]")
    print("   <= &in(A; B)%:[{A}]")
    print("   <- A |ref. [%D[0]=[%A[0]=%(a1)]], [%D[1]=[%A[1]=%(a2)]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%(b1), %B[1]=%(b2)]], [%D[1]=[%B[0]=%(b1), %B[1]=%(b2)]]]")
    
    result_simple_and_in = grouper.and_in([A_ref, B_ref], ['{A}', '{B}'], ['D'])
    print(f"\nResult shape: {result_simple_and_in.shape}")
    print(f"Result axes: {result_simple_and_in.axes}")
    print(f"Result data: {result_simple_and_in.tensor}")

    expected_result = "[[{'{A}': ['%(a1)'], '{B}': ['%(b1)', '%(b2)']}, {'{A}': ['%(a2)'], '{B}': ['%(b1)', '%(b2)']}]]"
    print(f"expected: {expected_result}")
    
    # Apply template processing
    result_simple_and_in_templated = grouper.and_in([A_ref, B_ref], ['{A}', '{B}'], ['D'], simple_and_template)
    print(f"\nTemplated result: {result_simple_and_in_templated.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("9. THREE REFERENCES - AND IN Pattern: [{A} and {B} and {C} in all {A}]")
    print("   |ref. [%[%{A}[:(a1)], %{B}[:(b1), %(b2)], %{C}[:(c1)]], %[%{A}[:(a2)], %{B}[:(b1), %(b2)], %{C}[:(c2)]]]")
    print("   <= &in(A; B; C)%:[{A}]")
    print("   <- A |ref. [%D[0]=[%A[0]=%(a1)]], [%D[1]=[%A[1]=%(a2)]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%(b1), %B[1]=%(b2)]], [%D[1]=[%B[0]=%(b1), %B[1]=%(b2)]]]")
    print("   <- C |ref. [%D[0]=[%C[0]=%(c1)]], [%D[1]=[%C[0]=%(c2)]]]")
    
    # Create a third reference C
    C_ref = Reference(
        axes=['D', 'C'],
        shape=(2, 1),
        initial_value=0
    )
    C_ref.tensor = [['%(c1)'], ['%(c2)']]
    
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data: {C_ref.tensor}")
    
    result_three_and_in = grouper.and_in([A_ref, B_ref, C_ref], ['{A}', '{B}', '{C}'], ['D'])
    print(f"\nResult shape: {result_three_and_in.shape}")
    print(f"Result axes: {result_three_and_in.axes}")
    print(f"Result data: {result_three_and_in.tensor}")
    
    expected_result = "[[{'{A}': ['%(a1)'], '{B}': ['%(b1)', '%(b2)'], '{C}': ['%(c1)']}, {'{A}': ['%(a2)'], '{B}': ['%(b1)', '%(b2)'], '{C}': ['%(c2)']}]]"
    print(f"expected: {expected_result}")
    
    # Apply template processing with three annotations
    three_ref_template = Template("A='${input1}', B='${input2}', C='${input3}'")
    result_three_and_in_templated = grouper.and_in([A_ref, B_ref, C_ref], ['{A}', '{B}', '{C}'], ['D'], three_ref_template)
    print(f"\nTemplated result: {result_three_and_in_templated.tensor}")
    
    print("\n" + "="*60 + "\n")
    

def demonstrate_multi_axis_example():
    """
    Demonstrate NormCodeGroup with complex multi-axis references.
    Shows how the system handles 3D data with multiple axes and complex grouping patterns.
    """
    print("=== Multi-Axis NormCodeGroup Demonstration ===\n")
    
    # Create a group instance
    grouper = Grouper()
    
    print("Multi-Axis Example: Student Performance Analysis")
    print("Scenario: Analyzing student performance across subjects, semesters, and assessment types")
    print("Axes: [student, subject, semester, assessment]")
    
    # Create a 4D reference for student grades across subjects, semesters, and assessment types
    grades_ref = Reference(
        axes=['student', 'subject', 'semester', 'assessment'],
        shape=(2, 3, 2, 2),  # 2 students, 3 subjects, 2 semesters, 2 assessment types
        initial_value=0
    )
    
    # Set sample grade data
    grades_ref.tensor = [
        [  # Student 0
            [  # Math
                [85, 92],  # Fall: exam, homework
                [90, 88]   # Spring: exam, homework
            ],
            [  # Science
                [78, 85],  # Fall: exam, homework
                [82, 80]   # Spring: exam, homework
            ],
            [  # English
                [92, 95],  # Fall: exam, homework
                [88, 90]   # Spring: exam, homework
            ]
        ],
        [  # Student 1
            [  # Math
                [91, 89],  # Fall: exam, homework
                [87, 85]   # Spring: exam, homework
            ],
            [  # Science
                [85, 82],  # Fall: exam, homework
                [89, 87]   # Spring: exam, homework
            ],
            [  # English
                [79, 76],  # Fall: exam, homework
                [84, 81]   # Spring: exam, homework
            ]
        ]
    ]
    
    print(f"DEBUG - Grades tensor after setting: {grades_ref.tensor}")
    print(f"DEBUG - Grades data property: {grades_ref.data}")
    
    # Create a 2D reference for assessment weights
    weights_ref = Reference(
        axes=['subject', 'assessment'],
        shape=(3, 2),  # 3 subjects, 2 assessment types
        initial_value=0
    )
    
    # Set assessment weights
    weights_ref.tensor = [
        [0.6, 0.4],  # Math: exams, homework
        [0.5, 0.5],  # Science: exams, homework
        [0.4, 0.6]   # English: exams, homework
    ]
    
    print(f"DEBUG - Weights tensor after setting: {weights_ref.tensor}")
    print(f"DEBUG - Weights data property: {weights_ref.data}")
    
    # Create a 1D reference for semester names
    semester_names_ref = Reference(
        axes=['semester'],
        shape=(2,),
        initial_value=0
    )
    
    semester_names_ref.tensor = ['Fall 2023', 'Spring 2024']
    
    print(f"\nReference 1 - Grades:")
    print(f"Shape: {grades_ref.shape}")
    print(f"Axes: {grades_ref.axes}")
    print(f"Sample data (Student 0, Math, Fall): {grades_ref.get(student=0, subject=0, semester=0)}")
    print(f"Sample data (Student 0, Math, Fall, exam): {grades_ref.get(student=0, subject=0, semester=0, assessment=0)}")
    
    print(f"\nReference 2 - Assessment Weights:")
    print(f"Shape: {weights_ref.shape}")
    print(f"Axes: {weights_ref.axes}")
    print(f"Data: {weights_ref.tensor}")
    
    print(f"\nReference 3 - Semester Names:")
    print(f"Shape: {semester_names_ref.shape}")
    print(f"Axes: {semester_names_ref.axes}")
    print(f"Data: {semester_names_ref.tensor}")
    
    print("\n" + "="*60)
    print("1. AND IN Pattern: Combine grades and weights by subject")
    print("   <= &in({grades};{weights})%:[{subject}]")
    
    # Create template for processing
    template = Template("Grades: ${input1}, Weights: ${input2}")
    
    # Debug: Let's see what happens when we get elements manually
    print(f"\nDEBUG - Testing manual get operations:")
    print(f"Grades get(subject=0): {grades_ref.get(subject=0)}")
    print(f"Grades get(student=0, subject=0): {grades_ref.get(student=0, subject=0)}")
    print(f"Grades get(student=0, subject=0, semester=0): {grades_ref.get(student=0, subject=0, semester=0)}")
    print(f"Grades get(student=0, subject=0, semester=0, assessment=0): {grades_ref.get(student=0, subject=0, semester=0, assessment=0)}")
    print(f"Weights get(subject=0): {weights_ref.get(subject=0)}")

    no_template_result = grouper.and_in(
        [grades_ref, weights_ref], 
        ['{grades}', '{weights}'], 
        ['subject']
    )
    print(f"\nNo template result: {no_template_result.tensor}") 
    
    result_and_in = grouper.and_in(
        [grades_ref, weights_ref], 
        ['{grades}', '{weights}'], 
        ['subject'], 
        template
    )
    
    print(f"\nResult shape: {result_and_in.shape}")
    print(f"Result axes: {result_and_in.axes}")
    print(f"Result data: {result_and_in.tensor}")
    
    print("\n" + "="*60)
    print("2. OR ACROSS Pattern: Flatten grades across students")
    print("   <= &across({grades})%:[{student}]")
    
    or_template = Template("Grade data: ${input1}")

    no_template_result = grouper.or_across(
        [grades_ref], 
        ['student']
    )
    print(f"\nNo template result: {no_template_result.tensor}") 
    
    result_or_across = grouper.or_across(
        [grades_ref], 
        ['student'], 
        or_template
    )
    
    print(f"\nResult shape: {result_or_across.shape}")
    print(f"Result axes: {result_or_across.axes}")
    print(f"Result data: {result_or_across.tensor}")
    
    print("\n" + "="*60)
    print("3. AND ONLY Pattern: Combine grades and weights without slicing")
    print("   <= &in({grades};{weights})")

    and_only_template = Template("Grades: ${input1}, Weights: ${input2}")
    
    no_template_result = grouper.and_in(
        [grades_ref, weights_ref], 
        ['{grades}', '{weights}']
    )
    print(f"\nNo template result: {no_template_result.tensor}") 

    result_and_only = grouper.and_in(
        [grades_ref, weights_ref], 
        ['{grades}', '{weights}'], 
        template=and_only_template
    )
    
    print(f"\nResult shape: {result_and_only.shape}")
    print(f"Result axes: {result_and_only.axes}")
    print(f"Result data: {result_and_only.tensor}")
    
    print("\n" + "="*60)
    print("4. OR ONLY Pattern: Flatten grades without slicing")
    print("   <= &across({grades})")
    
    or_only_template = Template("Flattened grades: ${input1}")

    no_template_result = grouper.or_across(
        [grades_ref], 
    )
    print(f"\nNo template result: {no_template_result.tensor}") 
    
    result_or_only = grouper.or_across(
        [grades_ref], 
        template=or_only_template
    )
    
    print(f"\nResult shape: {result_or_only.shape}")
    print(f"Result axes: {result_or_only.axes}")
    print(f"Result data: {result_or_only.tensor}")
    
    print("\n" + "="*60)
    print("5. Complex AND IN with Student and Subject")
    print("   <= &in({grades};{weights})%:[{student};{subject}]")
    
    
    complex_template = Template("Student-Subject: grades=${input1}, weights=${input2}")
    
    no_template_result = grouper.and_in(
        [grades_ref, weights_ref], 
        ['{grades}', '{weights}'], 
        ['subject']
    )
    print(f"\nNo template result: {no_template_result.tensor}") 

    result_complex = grouper.and_in(
        [grades_ref, weights_ref], 
        ['{grades}', '{weights}'], 
        ['subject'], 
        complex_template
    )
    
    print(f"\nResult shape: {result_complex.shape}")
    print(f"Result axes: {result_complex.axes}")
    print(f"Result data: {result_complex.tensor}")
    
    print("\n" + "="*60 + "\n")


def debug_element_action():
    """
    Debug function to test element_action behavior with the multi-axis data
    """
    print("=== Debug Element Action ===")
    
    # Create the same references as in the multi-axis example
    grades_ref = Reference(
        axes=['student', 'subject', 'semester', 'assessment'],
        shape=(2, 3, 2, 2),
        initial_value=0
    )
    grades_ref.tensor = [
        [  # Student 0
            [  # Math
                [85, 92],  # Fall: exam, homework
                [90, 88]   # Spring: exam, homework
            ],
            [  # Science
                [78, 85],  # Fall: exam, homework
                [82, 80]   # Spring: exam, homework
            ],
            [  # English
                [92, 95],  # Fall: exam, homework
                [88, 90]   # Spring: exam, homework
            ]
        ],
        [  # Student 1
            [  # Math
                [91, 89],  # Fall: exam, homework
                [87, 85]   # Spring: exam, homework
            ],
            [  # Science
                [85, 82],  # Fall: exam, homework
                [89, 87]   # Spring: exam, homework
            ],
            [  # English
                [79, 76],  # Fall: exam, homework
                [84, 81]   # Spring: exam, homework
            ]
        ]
    ]
    
    weights_ref = Reference(
        axes=['subject', 'assessment'],
        shape=(3, 2),
        initial_value=0
    )
    weights_ref.tensor = [
        [0.6, 0.4],  # Math: exams, homework
        [0.5, 0.5],  # Science: exams, homework
        [0.4, 0.6]   # English: exams, homework
    ]
    
    print("Grades reference:")
    print(f"  Axes: {grades_ref.axes}")
    print(f"  Shape: {grades_ref.shape}")
    print(f"  Sample data: {grades_ref.get(student=0, subject=0)}")
    
    print("\nWeights reference:")
    print(f"  Axes: {weights_ref.axes}")
    print(f"  Shape: {weights_ref.shape}")
    print(f"  Sample data: {weights_ref.get(subject=0)}")
    
    # Test cross product
    print("\nTesting cross product...")
    try:
        combined = cross_product([grades_ref, weights_ref])
        print(f"  Combined axes: {combined.axes}")
        print(f"  Combined shape: {combined.shape}")
        print(f"  Sample combined data: {combined.get(student=0, subject=0)}")
    except Exception as e:
        print(f"  Cross product error: {e}")
    
    # Test element_action with a simple function
    print("\nTesting element_action with simple function...")
    def simple_function(a, b):
        return f"Grades: {a}, Weights: {b}"
    
    try:
        result = element_action(simple_function, [grades_ref, weights_ref])
        print(f"  Result axes: {result.axes}")
        print(f"  Result shape: {result.shape}")
        print(f"  Sample result: {result.get(student=0, subject=0)}")
    except Exception as e:
        print(f"  Element action error: {e}")
        import traceback
        traceback.print_exc()


def debug_formal_actuator_perception():
    """
    Debug function to test formal_actuator_perception behavior with the multi-axis data
    """
    print("=== Debug Formal Actuator Perception ===")
    
    # Create the same references as in the multi-axis example
    grades_ref = Reference(
        axes=['student', 'subject', 'semester', 'assessment'],
        shape=(2, 3, 2, 2),
        initial_value=0
    )
    grades_ref.tensor = [
        [  # Student 0
            [  # Math
                [85, 92],  # Fall: exam, homework
                [90, 88]   # Spring: exam, homework
            ],
            [  # Science
                [78, 85],  # Fall: exam, homework
                [82, 80]   # Spring: exam, homework
            ],
            [  # English
                [92, 95],  # Fall: exam, homework
                [88, 90]   # Spring: exam, homework
            ]
        ],
        [  # Student 1
            [  # Math
                [91, 89],  # Fall: exam, homework
                [87, 85]   # Spring: exam, homework
            ],
            [  # Science
                [85, 82],  # Fall: exam, homework
                [89, 87]   # Spring: exam, homework
            ],
            [  # English
                [79, 76],  # Fall: exam, homework
                [84, 81]   # Spring: exam, homework
            ]
        ]
    ]
    
    weights_ref = Reference(
        axes=['subject', 'assessment'],
        shape=(3, 2),
        initial_value=0
    )
    weights_ref.tensor = [
        [0.6, 0.4],  # Math: exams, homework
        [0.5, 0.5],  # Science: exams, homework
        [0.4, 0.6]   # English: exams, homework
    ]

    semester_names_ref = Reference(
        axes=['semester'],
        shape=(2,),
        initial_value=0
    )
    semester_names_ref.tensor = ['Fall 2023', 'Spring 2024']

    assessment_names_ref = Reference(
        axes=['assessment'],
        shape=(2,),
        initial_value=0
    )
    assessment_names_ref.tensor = ['exam', 'homework']

    student_names_ref = Reference(
        axes=['student'],
        shape=(2,),
        initial_value=0
    )
    student_names_ref.tensor = ['John', 'Jane']

    subject_names_ref = Reference(
        axes=['subject'],
        shape=(3,),
        initial_value=0
    )
    subject_names_ref.tensor = ['Math', 'Science', 'English']

    weather_names_ref = Reference(
        axes=['subject','weather'],
        shape=(4,2,),
        initial_value=0
    )
    weather_names_ref.tensor = [
        ['Rainy','webnga'],
        ['Happy','df'],
        ['Rainy','webnga'],
        ['Happy','df']
    ]


    student_concept = Concept(
        name='{student}',
        context='student',
        reference=student_names_ref
    )
    subject_concept = Concept(
        name='{subject}',
        context='subject',
        reference=subject_names_ref
    )
    semester_concept = Concept(
        name='{semester}',
        context='semester',
        reference=semester_names_ref
    )
    assessment_concept = Concept(
        name='{assessment}',
        context='assessment',
        reference=assessment_names_ref
    )
    grades_concept = Concept(
        name='{grades}',
        context='grades',
        reference=grades_ref
    )
    weights_concept = Concept(
        name='{weights}',
        context='weights',
        reference=weights_ref
    )
    weather_concept = Concept(
        name='{weather}',
        context='weather',
        reference=weather_names_ref
    )


    log_concept(student_concept)
    log_concept(subject_concept)
    log_concept(semester_concept)
    log_concept(assessment_concept)
    log_concept(grades_concept)
    log_concept(weights_concept)
    log_concept(weather_concept)

    value_concepts = [grades_concept, weights_concept]
    context_concepts = [student_concept, subject_concept, semester_concept, assessment_concept, weather_concept]

    function_concept = Concept(
        name='&across({grades};{weights})%:[{weather}]',
        context='grades or weights across all weather',
        reference=None
    )

    function = formal_actuator_perception(function_concept, context_concepts, value_concepts)

    value_references = [c.reference for c in value_concepts]

    grouper = Grouper()
    manual_function_result = grouper.or_across(
        value_references,
        slice_axes=['subject','weather']
    )
    logger.debug(f"Manual function result: {manual_function_result}")

    function_result = function(value_references)
    logger.debug(f"===")
    logger.debug(f"Function result: {function_result.tensor} \n with shape: {function_result.shape} \n and axes: {function_result.axes}")
    logger.debug(f"Manual function result: {manual_function_result.tensor} \n with shape: {manual_function_result.shape} \n and axes: {manual_function_result.axes}")



if __name__ == "__main__":
    # Set logging to INFO level by default
    set_log_level('DEBUG')
    
    # Run the demonstration
    debug_formal_actuator_perception()


