from _concept import Concept
from _reference import Reference, cross_product, element_action, cross_action
from string import Template
import logging
import sys
from typing import Optional
import re
from copy import copy

def setup_logging(level=logging.INFO, log_file=None):
    """Setup logging configuration for the inference module"""
    # Create formatter
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    # )
    formatter = logging.Formatter(
        '[%(levelname)s] %(message)s - %(asctime)s - %(name)s'
    )

    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def all_grouping_demo_methods(sequence_name: str) -> dict:

    if sequence_name == "grouping":
        return {    
        "input_working_configurations": input_working_configurations,
        "output_working_configurations": output_working_configurations,
        "memorized_values_perception": memorized_values_perception,
        "formal_actuator_perception": formal_actuator_perception,
        "syntatical_perception_actuation": syntatical_perception_actuation,
        "memory_actuation": memory_actuation,
        "return_reference": return_reference
    }
    else:
        return {}


def strip_element_wrapper(element: str) -> str:
    """
    Strip %( and ) from a reference element.
    
    Args:
        element (str): A string that may be wrapped in %(...)
        
    Returns:
        str: The element with %( and ) removed if present
        
    Examples:
        >>> _strip_element_wrapper("%(1)")
        "1"
        >>> _strip_element_wrapper("%(::({1}<$({number})%_> add {2}<$({number})%_>))")
        "::({1}<$({number})%_> add {2}<$({number})%_>)"
        >>> _strip_element_wrapper("plain_text")
        "plain_text"
    """
    if element.startswith("%(") and element.endswith(")"):
        return element[2:-1]  # Remove first 2 chars (%() and last char ())
    return element

def wrap_element_wrapper(element: str) -> str:
    """
    Wrap an element in %(...)
    """
    return f"%({element})"


class Grouper:
    """
    A class that abstracts NormCode grouping patterns as functions of references.
    Provides methods for different grouping operations: simple_or, and_in, or_across, and_only, or_only.
    """
    
    def __init__(self, skip_value="@#SKIP#@"):
        """
        Initialize the Grouper.
        
        Args:
            skip_value (str): Value to use for missing/skip elements
        """
        self.skip_value = skip_value
    
    def find_share_axes(self, references):
        """
        Find the shared axes between all references.
        
        Args:
            references (list): List of Reference objects
            
        Returns:
            list: List of shared axis names
        """
        if not references:
            return []
        shared_axes = set(references[0].axes)
        for ref in references[1:]:
            shared_axes.intersection_update(ref.axes)
        return list(shared_axes)
    
    def flatten_element(self, reference):
        """
        Flatten the element of the reference.
        
        Args:
            reference (Reference): The reference to flatten
            
        Returns:
            Reference: A new reference with flattened elements
        """
        def flatten_all_list(nested_list):
            if not isinstance(nested_list, list):
                return [nested_list]
            return sum((flatten_all_list(item) for item in nested_list), [])
        
        return element_action(flatten_all_list, [reference])
    
    def annotate_element(self, reference, annotation_list):
        """
        Annotate elements with labels.
        
        Args:
            reference (Reference): The reference to annotate
            annotation_list (list): List of annotation labels
            
        Returns:
            Reference: A new reference with annotated elements
        """
        def annotate_list(lst):
            logger.debug(f"annotate_list received: {lst}")
            logger.debug(f"annotation_list: {annotation_list}")
            logger.debug(f"len(lst): {len(lst)}, len(annotation_list): {len(annotation_list)}")
            
            # The cross product result is a list where each element is a list of values
            # from each input reference. We need to map these to the annotation labels.
            if len(lst) != len(annotation_list):
                # If the lengths don't match, return skip value
                logger.debug(f"Length mismatch, returning skip value")
                return self.skip_value
            
            annotation_dict = {}
            for i, annotation in enumerate(annotation_list):
                annotation_dict[annotation] = lst[i]
            logger.debug(f"Created annotation_dict: {annotation_dict}")
            return annotation_dict
        
        return element_action(annotate_list, [reference])
    
    def create_unified_element_actuation(self, template, annotation_list=None):
        """
        Create a unified element actuation function for template processing.
        Handles both annotated and non-annotated cases.
        
        Args:
            template (Template): String template for processing
            annotation_list (list, optional): List of annotation labels. 
                                            If None, treats elements as simple values.
            
        Returns:
            function: Element actuation function
        """
        def element_actuation(element):
            logger.debug(f"element_actuation received element: {element}")
            logger.debug(f"element type: {type(element)}")
            return_string = ""
            
            # Handle both single element and list of elements
            if isinstance(element, list):
                elements = element
            else:
                elements = [element]
            
            for one_element in elements:
                logger.debug(f"Processing one_element: {one_element}")
                if annotation_list is not None:
                    # Annotated case: element is a dict with annotation keys
                    input_dict = {}
                    for i, annotation in enumerate(annotation_list):
                        logger.debug(f"Looking for annotation: {annotation}")
                        if annotation in one_element:
                            input_value = one_element[annotation]
                            logger.debug(f"Found input_value: {input_value}")
                            
                            # Handle the input value directly without Reference conversion
                            if isinstance(input_value, list):
                                # For lists, convert to a readable string representation
                                processed_value = str(input_value)
                                logger.debug(f"Converted list to string: {processed_value}")
                            else:
                                # For other types, convert to string
                                processed_value = str(input_value)
                                logger.debug(f"Converted to string: {processed_value}")
                            
                            input_dict[f"input{i+1}"] = processed_value
                        else:
                            # Handle missing annotation
                            logger.debug(f"Missing annotation: {annotation}")
                            input_dict[f"input{i+1}"] = self.skip_value
                    logger.debug(f"Final input_dict: {input_dict}")
                else:
                    # Non-annotated case: element is a simple value or list of values
                    if isinstance(one_element, list):
                        # Flatten and join multiple elements
                        format_string = ""
                        for base_element in one_element:
                            format_string += f"{str(base_element)}"
                            if base_element != one_element[-1]:
                                format_string += "; "
                        input_dict = {"input1": format_string}
                    else:
                        # Single element
                        input_dict = {"input1": str(one_element)}
                
                template_copy = copy(template)
                result_string = template_copy.safe_substitute(**input_dict) + " \n"
                logger.debug(f"Template result: {result_string}")
                return_string += result_string
            
            return return_string
        
        return element_actuation
    
    
    def and_in(self, references, annotation_list, slice_axes=None, template=None, pop=True):
        """
        Implement the AND patterns: 
        - AND IN: [{old expression} and {new expression} in all {old expression}] (when slice_axes provided)
        - AND ONLY: [{old expression} and {new expression}] (when slice_axes is None)
        
        Args:
            references (list): List of Reference objects to combine
            annotation_list (list): List of annotation labels
            slice_axes (list, optional): List of axes to slice by, the last axis will be removed. 
                                       If None, no slicing is performed (AND ONLY pattern).
            template (Template, optional): Template for processing results
            
        Returns:
            Reference: Processed reference with annotations
        """
        # Find shared axes
        shared_axes = self.find_share_axes(references)
        logger.debug(f"Shared axes: {shared_axes}")
        logger.debug(f"All reference axes: {[ref.axes for ref in references]}")
        
        # Slice references to shared axes
        sliced_refs = [ref.slice(*shared_axes) for ref in references]
        logger.debug(f"Sliced refs shapes: {[ref.shape for ref in sliced_refs]}")
        logger.debug(f"Sliced refs axes: {[ref.axes for ref in sliced_refs]}")
        logger.debug(f"Sliced refs sample data: {[ref.tensor for ref in sliced_refs]}")
        
        # Perform cross product
        result = cross_product(sliced_refs)
        logger.debug(f"Cross product result shape: {result.shape}")
        logger.debug(f"Cross product result axes: {result.axes}")
        logger.debug(f"Cross product result sample: {result.tensor}")
        
        # Annotate elements
        result = self.annotate_element(result, annotation_list)
        logger.debug(f"After annotation shape: {result.shape}")
        logger.debug(f"After annotation axes: {result.axes}")
        logger.debug(f"After annotation sample: {result.tensor}")

        # Slice by slice_axes if provided (AND IN pattern)
        if slice_axes is not None and len(slice_axes) > 0:
            if not isinstance(slice_axes[0], list):
                slice_axes = [slice_axes]

            preserve_axes = [axis for axis in result.axes if not any(axis in sublist for sublist in slice_axes)]
            
            slice_axes_copy = slice_axes.copy()  # Create a copy to avoid modifying the original
            if pop:
                # Pop the last element from each sublist
                for i in range(len(slice_axes_copy)):
                    if slice_axes_copy[i]:  # Check if sublist is not empty
                        slice_axes_copy[i].pop()


            # Find axes that are present in all sublists
            axes_in_all_groups = [axis for axis in result.axes if all(axis in sublist for sublist in slice_axes_copy)] if slice_axes_copy[0] else []

            final_slice_axes = preserve_axes + axes_in_all_groups
            result = result.slice(*final_slice_axes)
            logger.debug(f"After slice shape: {result.shape}")
            logger.debug(f"After slice axes: {result.axes}")
            logger.debug(f"After slice sample: {result.tensor}")
        
        # Apply template if provided
        if template:
            element_actuation = self.create_unified_element_actuation(
                template, 
                annotation_list
            )
            result = element_action(element_actuation, [result])
        
        return result
    
    def or_across(self, references, slice_axes=None, template=None, pop=True):
        """
        Implement the OR patterns:
        - OR ACROSS: [{old expression} or {new expression} across all {old expression}] (when slice_axes provided)
        - OR ONLY: [{old expression} or {new expression}] (when slice_axes is None)
        
        Args:
            references (list): List of Reference objects to combine
            slice_axes (list, optional): List of axes to slice by, the last axis will be removed.
                                       If None, no slicing is performed (OR ONLY pattern).
            template (Template, optional): Template for processing results
            
        Returns:
            Reference: Processed reference with flattened elements
        """
        # Find shared axes
        shared_axes = self.find_share_axes(references)
        
        # Slice references to shared axes
        sliced_refs = [ref.slice(*shared_axes) for ref in references]
        
        # Perform cross product
        result = cross_product(sliced_refs)
        
        # Slice by slice_axes if provided (OR ACROSS pattern)
        if slice_axes is not None and len(slice_axes) > 0:
            if not isinstance(slice_axes[0], list):
                slice_axes = [slice_axes]
                
            preserve_axes = [axis for axis in result.axes if not any(axis in sublist for sublist in slice_axes)]
            
            slice_axes_copy = slice_axes.copy()  # Create a copy to avoid modifying the original
            if pop:
                # Pop the last element from each sublist
                for i in range(len(slice_axes_copy)):
                    if slice_axes_copy[i]:  # Check if sublist is not empty
                        slice_axes_copy[i].pop()

            # Find axes that are present in all sublists
            axes_in_all_groups = [axis for axis in result.axes if all(axis in sublist for sublist in slice_axes_copy)] if slice_axes_copy[0] else []

            final_slice_axes = preserve_axes + axes_in_all_groups
            result = result.slice(*final_slice_axes)
        
        # Flatten elements
        result = self.flatten_element(result)
        
        # Apply template if provided
        if template:
            element_actuation = self.create_unified_element_actuation(template, None)
            result = element_action(element_actuation, [result])
        
        return result
    


def _parse_normcode_grouping(expr):
    """
    Parse a NormCode grouping expression to extract:
      - GroupMarker (after &)
      - Values in parentheses, separated by ;
      - Slice axis after %:
    Each value in parentheses and each axis after %: is treated as a whole (including braces).
    """
    # Match the GroupMarker and the values in parentheses
    match = re.match(r"&(\w+)\(([^)]*)\)", expr)
    if not match:
        raise ValueError("Invalid NormCode grouping expression format")
    group_marker = match.group(1)
    values_str = match.group(2)
    # Split values by ; and strip whitespace
    values = [v.strip() for v in values_str.split(';') if v.strip()]
    # Find the slice_axis after %: (always in format %:[...])
    slice_axis_match = re.search(r"%:(\[.*\])", expr)
    if slice_axis_match:
        # Extract the content inside brackets and split by semicolon
        bracket_content = slice_axis_match.group(1)[1:-1]  # Remove [ and ]
        slice_axis = [axis.strip() for axis in bracket_content.split(';') if axis.strip()]
    else:
        slice_axis = []
    return {
        "GroupMarker": group_marker,
        "Values": values,
        "SliceAxis": slice_axis
    }

def input_working_configurations(value_concepts:list[Concept], function_concept:Concept, concept_to_infer:Concept, all_working_configuration:dict):
    active_working_configuration = {}  

    for concept in value_concepts:
        active_working_configuration[concept.name] = all_working_configuration[concept.name]

    active_working_configuration[function_concept.name] = all_working_configuration[function_concept.name]

    active_working_configuration[concept_to_infer.name] = all_working_configuration[concept_to_infer.name]

    logger.debug(f"Active working configuration: {active_working_configuration}")

    return active_working_configuration

def output_working_configurations(concept_to_infer_with_reference):
    pass


def memorized_values_perception(working_configuration, value_concepts, function_concept):
    """Perform the memorized values perception"""
    logger.debug(f"Executing MVP step with value concepts: {value_concepts}")
    value_order = working_configuration[function_concept.name]["actuation"]["pta"]["value_order"]
    logger.debug(f"Value order: {value_order}")
    value_concepts_references: list[Optional[Reference | None]] = len(value_order) * [None] # type: ignore
    logger.debug(f"Value concepts references: {value_concepts_references}")

    for value_concept in value_concepts:
        raw_concept_reference = value_concept.reference
        logger.debug(f"Raw concept reference: {raw_concept_reference.tensor}")
        value_concept_index = int(value_order[value_concept.name])
        logger.debug(f"Value concept index: {value_concept_index}")
        concept_reference = element_action(strip_element_wrapper, [raw_concept_reference])
        logger.debug(f"Concept reference: {concept_reference.tensor}")
        value_concepts_references[value_concept_index] = concept_reference
    logger.debug(f"Value concepts: {[concept.name for concept in value_concepts]}")
    logger.debug(f"Value concepts references: {value_concepts_references}")
    return value_concepts_references


def formal_actuator_perception(function_concept, context_concepts, value_concepts):
    """Perform the formal actuator perception"""
    logger.debug(f"Executing FAP step with function concept: {function_concept.name}")

    parsed_normcode_grouping = _parse_normcode_grouping(function_concept.name)
    logger.debug(f"Parsed normcode grouping: {parsed_normcode_grouping}")

    if context_concepts is None:
        context_concepts = []

    context_concepts = [c for c in context_concepts if c.name in parsed_normcode_grouping["SliceAxis"]]
    logger.debug(f"Context concepts: {[c.name for c in context_concepts]}")

    context_axes = [c.reference.axes for c in context_concepts]
    logger.debug(f"Context axes: {context_axes}")

    value_concept_names = [c.name for c in value_concepts if c.name in parsed_normcode_grouping["Values"]]
    logger.debug(f"Value concept names: {value_concept_names}")

    grouper = Grouper()
    if parsed_normcode_grouping["GroupMarker"] == "in":
        grouping_actuated = lambda x: grouper.and_in(
            x, 
            value_concept_names, 
            slice_axes=context_axes,
        )
    elif parsed_normcode_grouping["GroupMarker"] == "across":
        grouping_actuated = lambda x: grouper.or_across(
            x, 
            slice_axes=context_axes,
        )
    else:
        raise ValueError(f"Invalid group marker: {parsed_normcode_grouping['GroupMarker']}")

    return grouping_actuated


def syntatical_perception_actuation(formal_actuator_function, perception_references):
    """Perform the syntatical perception actuation"""
    logger.debug(f"Executing SPA step with formal actuator function: {formal_actuator_function}")

    return formal_actuator_function(perception_references)


def memory_actuation(action_specification_perception):
    """Perform the memory actuation"""
    logger.debug("Executing MA step")
    action_specification_perception_wrapped = element_action(wrap_element_wrapper, [action_specification_perception])
    logger.debug(f"Action specification perception wrapped: {action_specification_perception_wrapped.tensor}")
    return action_specification_perception_wrapped  

def return_reference(action_specification_perception, concept_to_infer):
    """Perform the return reference"""
    logger.debug("Executing RR step")
    concept_to_infer.reference = action_specification_perception
    logger.debug(f"Concept to infer reference: {concept_to_infer.reference.tensor}")
    return concept_to_infer


if __name__ == "__main__":
    pass