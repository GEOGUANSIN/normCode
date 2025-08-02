from os import name
from _concept import Concept
from _reference import Reference, cross_product, element_action, cross_action
from string import Template
import logging
import sys
from typing import Optional, List, Dict, Any
import re
from copy import copy

def setup_logging(level=logging.INFO, log_file=None):
    """Setup logging configuration for the inference module"""
    # Create formatter
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

def all_quantification_demo_methods(sequence_name: str) -> dict:
    """Return all quantification demo methods for the given sequence"""
    if sequence_name == "quantification":
        return {    
            "input_working_configurations": input_working_configurations,
            "output_working_configurations": output_working_configurations,
            "memorized_values_perception": memorized_values_perception,
            "formal_actuator_perception": formal_actuator_perception,
            "group_perception": group_perception,
            "context_value_perception": context_value_perception,
            "actuator_value_perception": actuator_value_perception,
            "perception_tool_actuation": perception_tool_actuation,
            "grouping_actuation": grouping_actuation,
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
        >>> strip_element_wrapper("%(1)")
        "1"
        >>> strip_element_wrapper("%(::({1}<$({number})%_> add {2}<$({number})%_>))")
        "::({1}<$({number})%_> add {2}<$({number})%_>)"
        >>> strip_element_wrapper("plain_text")
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


def _parse_normcode_quantification(expr: str) -> dict:
    """

    Parse a NormCode quantification expression and extract its main components:

      - LoopBaseConcept: the main concept being iterated over (inside the parentheses after *every)
      - ViewAxis: one or more axes to view, specified in square brackets after %: (e.g., %:[axis1;axis2])
      - ConceptToInfer: one or more concepts to infer, specified in square brackets after the dot (e.g., .[concept1;concept2])
      - LoopIndex: (optional) a loop index, specified after @ (e.g., @(2))
      - InLoopConcept: (optional) a concept within the loop, specified after ^ (e.g., ^(concept))
      - CarryoverCondition: (optional) a carryover condition, specified after <* (e.g., <*1>)

    Each axis or concept is treated as a whole, including any braces or special characters.
    Multiple axes or concepts are separated by semicolons (;).

    
    Args:
        expr (str): The quantification expression to parse
        
    Returns:
        dict: Dictionary containing parsed components
    
    Examples:
        >>> _parse_normcode_quantification("*every({loop_base})%:[{view_axis1};{view_axis2}].[{concept1}?;{concept2}?]@(2)^({concept3}<*1>)")
        {
            "LoopBaseConcept": "{loop_base}",
            "ViewAxis": ["{view_axis1}", "{view_axis2}"],
            "ConceptToInfer": ["{concept1}?", "{concept2}?"],
            "LoopIndex": "2",
            "InLoopConcept": {"*{concept3}": 1}
        }
    """
    logger.debug(f"Parsing quantification expression: {expr}")
    
    # Initialize result dictionary
    result: Dict[str, Any] = {
        "LoopBaseConcept": None,
        "ViewAxis": [],
        "ConceptToInfer": [],
        "LoopIndex": None,
        "InLoopConcept": None
    }
    try:
        # Match the basic *every pattern: *every(loopBaseConcept)%:[viewAxis].[conceptToInfer]
        basic_pattern = r"\\*every\\(([^)]+)\\)%:(\\[[^\]]+\])\\.(\\[[^\]]+\])"
        basic_match = re.match(basic_pattern, expr)
        if not basic_match:
            raise ValueError(f"Invalid quantification expression format: {expr}")
        # Extract basic components
        result["LoopBaseConcept"] = basic_match.group(1).strip()
        # Extract ViewAxis and split by semicolon
        view_axis_str = basic_match.group(2).strip()
        if view_axis_str.startswith('[') and view_axis_str.endswith(']'):
            view_axis_content = view_axis_str[1:-1]  # Remove [ and ]
            result["ViewAxis"] = [axis.strip() for axis in view_axis_content.split(';') if axis.strip()]
        else:
            result["ViewAxis"] = [view_axis_str]
        # Extract ConceptToInfer and split by semicolon
        concept_to_infer_str = basic_match.group(3).strip()
        if concept_to_infer_str.startswith('[') and concept_to_infer_str.endswith(']'):
            concept_content = concept_to_infer_str[1:-1]  # Remove [ and ]
            result["ConceptToInfer"] = [concept.strip() for concept in concept_content.split(';') if concept.strip()]
        else:
            result["ConceptToInfer"] = [concept_to_infer_str]
        logger.debug(f"Basic components extracted: LoopBaseConcept={result['LoopBaseConcept']}, ViewAxis={result['ViewAxis']}, ConceptToInfer={result['ConceptToInfer']}")
        # Check for optional LoopIndex after @
        loop_index_pattern = r"@\\(([^)]+)\\)"
        loop_index_match = re.search(loop_index_pattern, expr)
        if loop_index_match:
            result["LoopIndex"] = loop_index_match.group(1).strip()
            logger.debug(f"LoopIndex extracted: {result['LoopIndex']}")
        # Check for optional InLoopConcept and CarryoverCondition after ^
        # Example: ^({concept3}<*1>)
        in_loop_pattern = r"\\^\\(([^<)]+)(?:<\\*([0-9]+)>)?\\)"
        in_loop_match = re.search(in_loop_pattern, expr)
        if in_loop_match:
            in_loop_concept = in_loop_match.group(1).strip()
            carryover = in_loop_match.group(2)
            if carryover is not None:
                # Return as a dict: {"*{concept3}": 1}
                result["InLoopConcept"] = {f"*{in_loop_concept}": int(carryover)}
            else:
                result["InLoopConcept"] = in_loop_concept
            logger.debug(f"InLoopConcept extracted: {result['InLoopConcept']}")
        logger.debug(f"Final parsed result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error parsing quantification expression '{expr}': {str(e)}")
        raise ValueError(f"Failed to parse quantification expression: {expr}")

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

class Quantifier:
    """
    A class that handles quantification processing for *every operator.
    Initialized with a workspace dictionary.
    """
    
    def __init__(self, workspace: dict, loop_base_concept_name: str, loop_concept_index: int = 0):
        """
        Initialize the Quantifier with a workspace dictionary.
        
        Args:
            workspace (dict): The workspace dictionary containing quantification state
        """
        self.workspace = workspace
        logger.debug(f"Initialized Quantifier with workspace: {workspace}")
        self.loop_base_concept_name = loop_base_concept_name
        self._initiate_subworkspace(loop_base_concept_name, loop_concept_index)

        # initiate the workspace for a specific CONCEPT's reference (after GP)
    def _initiate_subworkspace(self, loop_base_concept_name, loop_concept_index=0):
        """
        Initiate the workspace for a to_loop_elements
        """
        self.workspace_key = f"{loop_concept_index}_{loop_base_concept_name}"
        if self.workspace_key not in self.workspace.keys():
            self.workspace[self.workspace_key] = {}
        self.current_subworkspace = self.workspace[self.workspace_key]

    def _get_list_at_index(self, input_list, index):
        """
        Helper function to retrieve a list at a specific index.
        
        Args:
            input_list: The input list (can be nested)
            index (int): The index to retrieve
            
        Returns:
            The element at the specified index, or None if index is out of bounds
            
        Examples:
            >>> _get_list_at_index([1, 2, 3], 1)
            2
            >>> _get_list_at_index([[1, 2], [3, 4]], 0)
            [1, 2]
            >>> _get_list_at_index([1, 2, 3], 5)
            None
        """
        try:
            if isinstance(input_list, list) and 0 <= index < len(input_list):
                return input_list[index]
            else:
                return None
        except (IndexError, TypeError):
            return None

    def _flatten_list(self, nested_list):
        """
        Helper function to flatten a nested list recursively.
        
        Args:
            nested_list: The input list (can be deeply nested)
            
        Returns:
            list: A flattened list containing all elements
            
        Examples:
            >>> _flatten_list([1, [2, 3], [4, [5, 6]]])
            [1, 2, 3, 4, 5, 6]
            >>> _flatten_list([[1, 2], [3, 4]])
            [1, 2, 3, 4]
            >>> _flatten_list([1, 2, 3])
            [1, 2, 3]
        """
        flattened = []
        
        def _flatten_recursive(item):
            if isinstance(item, list):
                for element in item:
                    _flatten_recursive(element)
            else:
                flattened.append(item)
        
        _flatten_recursive(nested_list)
        return flattened
        

    def _check_new_base_element_by_looped_base_element(self, current_looped_element_reference, loop_base_concept_name):
        """
        Check if the new current looped_element is new by comparing with existing elements in workspace.
        
        Args:
            current_looped_element_reference: The current element reference to check
            loop_base_concept_name (str): The name of the loop base concept to check against
            
        Returns:
            bool: True if the element is new (not found in workspace), False otherwise
        """
        # Use the same logic as _check_all_base_elements_looped but for a single element
        element_found = False
        
        for loop_index in self.current_subworkspace.keys():
            if (loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                current_looped_element_reference in self.current_subworkspace[loop_index][loop_base_concept_name]):
                element_found = True
                break
        
        # Return True if element is NOT found (i.e., it's new)
        return not element_found

    def _check_index_of_current_looped_base_element(self, looped_base_reference):
        """
        Check if there are any existing loop indices that have the same reference as the looped_base_reference.
        If found, return that index; otherwise, get the next available loop index.
        
        Args:
            looped_base_reference: The reference to check for
            
        Returns:
            int: The existing index if found, or the next available loop index
        """
        # Check for existing loop indices with the same reference
        for existing_loop_index in self.current_subworkspace.keys():
            if (self.loop_base_concept_name in self.current_subworkspace[existing_loop_index] and 
                self.current_subworkspace[existing_loop_index][self.loop_base_concept_name] == looped_base_reference):
                return existing_loop_index
        
        # If no existing index found, get the next available loop index
        return self._get_next_loop_index()

    def _get_next_loop_index(self):
        """
        Helper function to get the next available loop index in the current subworkspace.
        
        Returns:
            int: The next available loop index
        """
        new_loop_index = 0
        for existing_loop_index in self.current_subworkspace.keys():
            if existing_loop_index > new_loop_index:
                new_loop_index = existing_loop_index
        return new_loop_index + 1

    def store_new_base_element(self, looped_base_reference):
        """
        Update the workspace according to some references and a loopedElements.
        
        Args:
            looped_base_reference: The base reference to check against
            
        Returns:
            int: The loop index where the element was stored
        """
        # Check if this base reference already exists in the workspace
        loop_index = self._check_index_of_current_looped_base_element(looped_base_reference)
             
        # Store the concept reference
        self.current_subworkspace[loop_index][self.loop_base_concept_name] = looped_base_reference
        
        return loop_index


    def store_new_in_loop_element(self, looped_base_reference, looped_concept_name, looped_concept_reference):
        """
        Update the workspace according to some references and a loopedElements.
        
        Args:
            looped_base_reference: The base reference to check against
            looped_concept_name (str): The name of the concept to store
            looped_concept_reference: The reference to store for the concept
            
        Returns:
            int: The loop index where the element was stored
        """
        # Check if this base reference already exists in the workspace
        loop_index = self._check_index_of_current_looped_base_element(looped_base_reference)
        
        # Initialize the loop index entry if it doesn't exist
        if loop_index not in self.current_subworkspace:
            raise ValueError(f"The {looped_base_reference} is not in the current_subworkspace")
        
        # Store the concept reference
        self.current_subworkspace[loop_index][looped_concept_name] = looped_concept_reference
        
        return loop_index

    def combine_processed_elements(self, looped_concept):
        """
        Combine the processed elements into a single reference.
        
        Args:
            looped_concept (str): The name of the concept to combine
            
        Returns:
            Reference: Combined reference from all processed elements
            
        Raises:
            ValueError: If the concept is not found in any loop index
        """
        all_references = []
        
        for loop_index in self.current_subworkspace.keys():
            if looped_concept in self.current_subworkspace[loop_index].keys():
                all_references.append(self.current_subworkspace[loop_index][looped_concept])
            else:
                raise ValueError(f"The {looped_concept} is not in the current_subworkspace at loop_index {loop_index}")
        
        if not all_references:
            raise ValueError(f"No references found for concept {looped_concept} in the workspace")
        
        combined_reference = cross_product(all_references)
        return combined_reference


    def retireve_next_base_element(self, to_loop_element_reference):
        """
        Retrieve the next element from the current_subworkspace.

        Args:
            to_loop_element_reference: Reference containing the elements to loop over.

        Returns:
            tuple: (current_to_loop_element_reference, current_loop_index)
                - current_to_loop_element_reference: The next element reference to process.
                - current_loop_index: The index of the next element.

        This method iterates through the elements in to_loop_element_reference and returns the next element
        that has not yet been processed/stored in the current_subworkspace for the given loop_base_concept_name.
        If all elements have been processed or skipped, returns (None, None).
        """

        current_loop_index = 0
        while True:
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            if all(e is None or e == "@#SKIP#@" for e in elements):
                break

            for loop_index in self.current_subworkspace.keys():
                if self.loop_base_concept_name in self.current_subworkspace[loop_index].keys():
                    if to_loop_element_reference in self.current_subworkspace[loop_index][self.loop_base_concept_name]:
                        current_loop_index += 1
                        continue
                    else:
                        return current_to_loop_element_reference, current_loop_index
                else:
                    raise ValueError(f"The {self.loop_base_concept_name} is not in the current_subworkspace")

        return None, None


    def check_all_base_elements_looped(self, to_loop_element_reference, in_loop_element_name=None):
        """
        Check if all elements in to_loop_element_reference have records in the workspace.
        Optionally also check if in_loop_element_name exists under each index.
        
        Args:
            to_loop_element_reference: Reference containing all elements to check
            in_loop_element_name (str, optional): Name of the in-loop element to check for under each index
            
        Returns:
            bool: True if all elements have records in workspace (and in_loop_element if specified), False otherwise
            
        Examples:
            >>> _check_all_elements_in_workspace(ref_with_elements, "digit_position")
            True  # if all elements are found in workspace
            >>> _check_all_elements_in_workspace(ref_with_elements, "digit_position", "in_loop_concept")
            True  # if all elements and in_loop_concept are found in workspace
            >>> _check_all_elements_in_workspace(ref_with_elements, "digit_position")
            False  # if any element is missing from workspace
        """
        current_loop_index = 0
        
        while True:
            # Create current_to_loop_element_reference for this index
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            
            # Check if we've reached the end (all None or skip values)
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            if all(e is None or e == "@#SKIP#@" for e in elements):
                current_loop_index += 1
                break
            
            # Check if this element exists in the workspace
            element_found = False
            matching_loop_index = None
            
            for loop_index in self.current_subworkspace.keys():
                if (self.loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                    current_to_loop_element_reference in self.current_subworkspace[loop_index][self.loop_base_concept_name]):
                    element_found = True
                    matching_loop_index = loop_index
                    break
            
            # If any element is not found, return False
            if not element_found:
                return False
            
            # If in_loop_element_name is specified, check if it exists under the matching loop index
            if in_loop_element_name is not None and matching_loop_index is not None:
                if in_loop_element_name not in self.current_subworkspace[matching_loop_index].keys():
                    logger.debug(f"In-loop element '{in_loop_element_name}' not found in loop index {matching_loop_index}")
                    return False
            
            current_loop_index += 1
        
        # All elements were found (and in_loop_element if specified)
        return True

    def combine_all_looped_elements_by_concept(self, to_loop_element_reference, concept_name: str):
        """
        Combine all looped elements for a specific concept name according to the to_loop_element_reference.
        
        Args:
            to_loop_element_reference: Reference containing all elements to loop over
            concept_name (str): Name of the concept to combine elements for
            
        Returns:
            Reference: Combined reference of all looped elements for the specified concept
            
        Examples:
            >>> combined_ref = quantifier.combine_all_looped_elements_by_concept(to_loop_ref, "digit_pairs")
            >>> print(combined_ref.tensor)
            # Returns combined reference of all digit_pairs elements
        """
        current_loop_index = 0
        all_concept_references = []
        
        while True:
            # Create current_to_loop_element_reference for this index
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            
            # Check if we've reached the end (all None or skip values)
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            if all(e is None or e == "@#SKIP#@" for e in elements):
                current_loop_index += 1
                break
            
            # Find the matching loop index for this element
            matching_loop_index = None
            for loop_index in self.current_subworkspace.keys():
                if (self.loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                    current_to_loop_element_reference in self.current_subworkspace[loop_index][self.loop_base_concept_name]):
                    matching_loop_index = loop_index
                    break
            
            # If matching loop index found and concept exists, add to collection
            if matching_loop_index is not None and concept_name in self.current_subworkspace[matching_loop_index].keys():
                concept_reference = self.current_subworkspace[matching_loop_index][concept_name]
                all_concept_references.append(concept_reference)
                logger.debug(f"Added concept reference for index {matching_loop_index}: {concept_reference.tensor}")
            else:
                logger.warning(f"Concept '{concept_name}' not found for loop index {matching_loop_index}")
            
            current_loop_index += 1
        
        # Combine all collected references
        if all_concept_references:
            combined_reference = cross_product(all_concept_references)
            logger.debug(f"Combined {len(all_concept_references)} references for concept '{concept_name}'")
            return combined_reference
        else:
            logger.warning(f"No references found for concept '{concept_name}'")
            return None

    def retrieve_next_in_loop_element(self, concept_name: str, mode: str = 'carry_over', current_loop_index: int = 0, carry_index: int = 0):
        """
        Retrive the next element from the current_subworkspace
        """
        if mode == 'carry_over':
            if current_loop_index > carry_index:
                concept_reference = self.current_subworkspace[current_loop_index - carry_index][concept_name]
            else:
                concept_reference = None
        
        return concept_reference

# Quantification sequence step implementations

def input_working_configurations(value_concepts: List[Concept], function_concept: Concept, 
                                concept_to_infer: Concept, all_working_configuration: dict):
    """
    Perform input working configurations for quantification sequence.
    
    Args:
        value_concepts (List[Concept]): Value concepts
        function_concept (Concept): Function concept
        concept_to_infer (Concept): Concept to infer
        all_working_configuration (dict): All working configuration
        
    Returns:
        dict: Working configuration
    """
    logger.debug("Executing input working configurations for quantification")
    logger.debug(f"Value concepts: {[concept.name for concept in value_concepts]}")
    logger.debug(f"Function concept: {function_concept.name}")
    logger.debug(f"Concept to infer: {concept_to_infer.name}")
    
    # TODO: Implement input working configuration logic
    return all_working_configuration


def output_working_configurations(working_configuration, function_concept, workspace, loop_base_concept_name, to_loop_elements, concept_to_infer):
    """
    Check if all to loop elements are present in the workspace and set the completion status.
    
    Args:
        working_configuration (dict): Working configuration
        function_concept (Concept): Function concept
        workspace (dict): Workspace
        loop_base_concept_name (str): Loop base concept name
        to_loop_elements (List[Any]): To loop elements
        concept_to_infer (Concept): Concept to infer
        
    Returns:
        None
    """
    logger.debug("Executing output working configurations for quantification")
    logger.debug(f"Function concept: {function_concept.name}")
    
    logger.debug("Executing status check for quantification")
    logger.debug(f"To loop elements: {to_loop_elements}")
    logger.debug(f"Concept to infer: {concept_to_infer.name}")
    
    processor = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    status = processor.check_all_base_elements_looped(to_loop_elements, concept_to_infer.name)
    working_configuration[function_concept.name]["completion_status"] = status
    logger.debug(f"Completion status: {status}")
    
    return working_configuration


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

#FGAP
def formal_actuator_perception(function_concept, context_concepts):
    """
    Perform formal actuator perception for quantification sequence.
    
    Args:
        function_concept (Concept): Function concept
        context_concepts (List[Concept]): Context concepts
        
    Returns:
        function: Formal actuator function
    """
    logger.debug(f"Executing FAP step with function concept: {function_concept.name}")

    parsed_normcode_quantification = _parse_normcode_quantification(function_concept.name)
    logger.debug(f"Parsed normcode quantification: {parsed_normcode_quantification}")

    if context_concepts is None:
        context_concepts = []

    # Filter context concepts based on ViewAxis (similar to SliceAxis in grouping)
    context_concepts = [c for c in context_concepts if c.name in parsed_normcode_quantification["ViewAxis"]]
    logger.debug(f"Context concepts: {[c.name for c in context_concepts]}")

    context_axes = [c.reference.axes for c in context_concepts]
    logger.debug(f"Context axes: {context_axes}")

    grouper = Grouper()
    # For quantification, we always use or_across pattern
    quantification_actuated = lambda x: grouper.or_across(
        x, 
        slice_axes=context_axes,
    )

    return quantification_actuated, parsed_normcode_quantification


def group_perception(perception_references, formal_actuator_function):
    """
    Perform group perception for quantification sequence.
    
    Args:
        perception_references (List[Reference]): Perception references
        formal_actuator_function: The formal actuator function from FAP
        
    Returns:
        Reference: Processed perception references
    """
    logger.debug(f"Executing GP step with formal actuator function: {formal_actuator_function}")

    return formal_actuator_function(perception_references)


#PTA
def perception_tool_actuation(parsed_normcode_quantification, workspace, loop_base_concept_name, to_loop_elements,
                          current_loop_base_element, concept_to_infer_name:str, current_loop_element, context_concepts:list[Concept]):
    """
    Perform perception tool actuation for quantification sequence.
    
    Args:
        to_loop_elements (List[Any], optional): To loop elements
        current_loop_element (Any, optional): Current loop element
        workspace (dict, optional): Workspace
        
    Returns:
        Dict[str, Any]: Updated workspace
    """
    
    quantifier = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    quantifier.store_new_base_element(current_loop_base_element)
    current_loop_base_element, current_loop_index = quantifier.retireve_next_base_element(to_loop_elements)

    quantifier.store_new_in_loop_element(current_loop_base_element, concept_to_infer_name, current_loop_element)

    current_in_loop_elements = []
    for context_concept in context_concepts:
        if context_concept.name in parsed_normcode_quantification["inLoopConcept"]:
            quantifier.store_new_in_loop_element(current_loop_base_element, context_concept.name, context_concept.reference)
            current_loop_index = parsed_normcode_quantification["inLoopConcept"][context_concept.name]
            current_in_loop_elements.append(quantifier.retrieve_next_in_loop_element(context_concept.name, current_loop_index))

    return current_loop_base_element, current_in_loop_elements


# CVP
def context_value_perception(current_loop_base_concept, workspace, loop_base_concept_name):
    """
    Perform context value perception for quantification sequence.
    
    Args:
        working_configuration (dict): Working configuration
        current_loop_base_concept (Concept): Current loop base concept
        quantifier_workspace (dict): Workspace for the Quantifier
        
    Returns:
        Any: Current loop element
    """
    logger.debug("Executing context value perception for quantification")
    logger.debug(f"Current loop base concept: {current_loop_base_concept.name}")
    
    # Initialize the Quantifier with the provided workspace
    processor = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    
    # Extract current element from reference
    current_element = None
    if current_loop_base_concept.reference:
        current_element = current_loop_base_concept.reference.get()
        
    # Check if the current element is new using Quantifier's method
    if current_element and processor._check_new_base_element_by_looped_base_element(current_element, current_loop_base_concept.name):
        logger.debug("New element detected in context value perception")
        return current_element, True
    else:
        logger.debug("Element is not new or no element found")
        return None, False


# AVP
def actuator_value_perception(function_concept):
    """
    Perform actuator value perception for quantification sequence.
    
    Args:
        function_concept (Concept): Function concept
        
    Returns:
        Any: Current concept element
    """
    logger.debug("Executing actuator value perception for quantification")
    logger.debug(f"Function concept: {function_concept.name}")
    
    if function_concept.reference:
        return function_concept.reference.get()
    
    return None



def grouping_actuation(workspace, loop_base_concept_name, to_loop_elements_reference, concept_to_infer):
    """
    Perform grouping actuation for quantification sequence.
    
    Args:
        working_configuration (dict): Working configuration
        processed_elements (List[Any]): Processed elements
        view_axis (str): View axis
        
    Returns:
        Reference: Combined reference
    """
    logger.debug("Executing grouping actuation for quantification")
    logger.debug(f"Concept to infer: {concept_to_infer.name}")
    logger.debug(f"To loop elements reference: {to_loop_elements_reference}")
    
    processor = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    combined_reference = processor.combine_all_looped_elements_by_concept(to_loop_elements_reference, concept_to_infer.name)
    
    return combined_reference


def memory_actuation(combined_reference, concept_to_infer):
    """
    Perform memory actuation for quantification sequence.
    """
    logger.debug("Executing memory actuation for quantification")
    logger.debug(f"Combined reference: {combined_reference}")
    logger.debug(f"Concept to infer: {concept_to_infer.name}")
    
    # TODO: Implement memory actuation logic
    pass

def return_reference(combined_reference, concept_to_infer):
    """
    Perform return reference for quantification sequence.
    
    Args:
        working_configuration (dict): Working configuration
        stored_reference (Reference): Stored reference
        concept_to_infer (Concept): Concept to infer
        
    Returns:
        Concept: Concept to infer with reference
    """
    logger.debug("Executing return reference for quantification")
    logger.debug(f"Combined reference: {combined_reference}")
    logger.debug(f"Concept to infer: {concept_to_infer.name}")
    
    # TODO: Implement return reference logic
    concept_to_infer.reference = combined_reference
    
    return concept_to_infer
