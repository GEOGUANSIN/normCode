from os import name
from _concept import Concept
from _reference import Reference, cross_product, element_action, cross_action
from string import Template
import logging
import sys
from typing import Optional, List, Dict, Any, Tuple
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
            "formal_actuator_perception": formal_actuator_perception,
            "group_perception": group_perception,
            "context_value_perception": context_value_perception,
            "actuator_value_perception": actuator_value_perception,
            "perception_tool_actuation": perception_tool_actuation,
            "grouping_actuation": grouping_actuation,
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
        basic_pattern = r"\*every\(([^)]+)\)%:\[([^\]]+)\]\.\[([^\]]+)\]"
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
    A class that handles quantification processing for operators in a workspace.
    
    The Quantifier manages the state of looped elements and their references,
    providing methods to store, retrieve, and combine references across iterations.
    
    Key Features:
    - Manages a workspace dictionary to track quantification state
    - Handles nested element references and loop indices
    - Provides utilities for flattening and combining references
    
    Args:
        workspace (dict): Dictionary containing quantification state
        loop_base_concept_name (str): Name of the base concept being looped over
        loop_concept_index (int, optional): Starting loop index (default: 0)
    """
    
    def __init__(self, workspace: dict, loop_base_concept_name: str, loop_concept_index: int = 0):
        """
        Initialize the Quantifier with a workspace and base concept.
        
        Args:
            workspace (dict): Dictionary to store quantification state
            loop_base_concept_name (str): Name of the base concept being looped over
            loop_concept_index (int, optional): Starting index for the loop (default: 0)
        """
        self.workspace = workspace
        logger.debug(f"[Quantifier.__init__] Initialized with workspace keys: {list(workspace.keys())}, loop_base_concept_name: {loop_base_concept_name}, loop_concept_index: {loop_concept_index}")
        self.loop_base_concept_name = loop_base_concept_name
        self._initiate_subworkspace(loop_base_concept_name, loop_concept_index)

        # initiate the workspace for a specific CONCEPT's reference (after GP)
    def _initiate_subworkspace(self, loop_base_concept_name: str, loop_concept_index: int = 0) -> None:
        """
        Initialize a subworkspace for a specific concept and loop index.
        
        Creates a workspace key in the format "{loop_index}_{concept_name}"
        and initializes the current subworkspace.
        
        Args:
            loop_base_concept_name (str): Name of the base concept
            loop_concept_index (int, optional): Loop index (default: 0)
        """
        self.workspace_key = f"{loop_concept_index}_{loop_base_concept_name}"
        if self.workspace_key not in self.workspace.keys():
            self.workspace[self.workspace_key] = {}
        self.current_subworkspace = self.workspace[self.workspace_key]
        logger.debug(f"[Quantifier._initiate_subworkspace] workspace_key: {self.workspace_key}, current_subworkspace keys: {list(self.current_subworkspace.keys())}")
        self._log_current_subworkspace_tensors()

    def _get_list_at_index(self, input_list: list, index: int) -> Optional[Any]:
        """
        Retrieve an element from a list at a specific index.
        
        Handles nested lists and out-of-bounds indices.
        
        Args:
            input_list: Input list (can be nested)
            index (int): Index to retrieve
            
        Returns:
            Element at index or None if index is invalid
        """
        logger.debug(f"[Quantifier._get_list_at_index] input_list type: {type(input_list)}, index: {index}")
        try:
            if isinstance(input_list, list) and 0 <= index < len(input_list):
                logger.debug(f"[Quantifier._get_list_at_index] Returning element at index {index}: {input_list[index]}")
                return input_list[index]
            else:
                logger.debug(f"[Quantifier._get_list_at_index] Index {index} out of bounds or input is not a list.")
                return None
        except (IndexError, TypeError) as e:
            logger.error(f"[Quantifier._get_list_at_index] Exception: {e}")
            return None

    def _flatten_list(self, nested_list: list) -> list:
        """
        Recursively flatten a nested list.
        
        Args:
            nested_list: Input list (can be deeply nested)
            
        Returns:
            list: Flattened single-level list
        """
        logger.debug(f"[Quantifier._flatten_list] Flattening nested_list: {nested_list}")
        flattened = []
        def _flatten_recursive(item):
            if isinstance(item, list):
                for element in item:
                    _flatten_recursive(element)
            else:
                flattened.append(item)
        _flatten_recursive(nested_list)
        logger.debug(f"[Quantifier._flatten_list] Result: {flattened}")
        return flattened
        

    def _check_new_base_element_by_looped_base_element(self, current_looped_element_reference: Reference, loop_base_concept_name: str) -> bool:
        """
        Check if an element is new by comparing with workspace entries.
        
        Args:
            current_looped_element_reference: Reference to check
            loop_base_concept_name (str): Base concept name to match against
            
        Returns:
            bool: True if element is new (not in workspace), False otherwise
        """
        logger.debug(f"[Quantifier._check_new_base_element_by_looped_base_element] Checking for new element: tensor={getattr(current_looped_element_reference, 'tensor', None)}, loop_base_concept_name: {loop_base_concept_name}")
        element_found = False
        for loop_index in self.current_subworkspace.keys():
            if (loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                current_looped_element_reference.tensor == self.current_subworkspace[loop_index][loop_base_concept_name].tensor):
                logger.debug(f"[Quantifier._check_new_base_element_by_looped_base_element] Found existing element at loop_index: {loop_index}")
                element_found = True
                break
        logger.debug(f"[Quantifier._check_new_base_element_by_looped_base_element] Is new: {not element_found}")
        return not element_found

    def _check_index_of_current_looped_base_element(self, looped_base_reference: Reference) -> int:
        """
        Find existing loop index for a reference or get next available index.
        
        Args:
            looped_base_reference: Reference to find
            
        Returns:
            int: Existing index if found, next available index otherwise
        """
        logger.debug(f"[Quantifier._check_index_of_current_looped_base_element] Checking for looped_base_reference.tensor: {getattr(looped_base_reference, 'tensor', None)}")
        for existing_loop_index in self.current_subworkspace.keys():
            if (self.loop_base_concept_name in self.current_subworkspace[existing_loop_index] and 
                self.current_subworkspace[existing_loop_index][self.loop_base_concept_name].tensor == looped_base_reference.tensor):
                logger.debug(f"[Quantifier._check_index_of_current_looped_base_element] Found at index: {existing_loop_index}")
                return existing_loop_index
        next_index = self._get_next_loop_index()
        logger.debug(f"[Quantifier._check_index_of_current_looped_base_element] Not found, returning next available index: {next_index}")
        return next_index

    def _get_next_loop_index(self) -> int:
        """
        Get the next available loop index in the subworkspace.
        """
        logger.debug(f"[Quantifier._get_next_loop_index] Current subworkspace keys: {list(self.current_subworkspace.keys())}")
        new_loop_index = 0
        for existing_loop_index in self.current_subworkspace.keys():
            if existing_loop_index > new_loop_index:
                new_loop_index = existing_loop_index
        logger.debug(f"[Quantifier._get_next_loop_index] Next loop index: {new_loop_index + 1}")
        return new_loop_index + 1

    def store_new_base_element(self, looped_base_reference: Reference) -> int:
        """
        Store a new base element reference in the workspace.
        
        Args:
            looped_base_reference: Reference to store
            
        Returns:
            int: Loop index where element was stored
        """
        logger.debug(f"[Quantifier.store_new_base_element] Storing base element: tensor={getattr(looped_base_reference, 'tensor', None)}")
        loop_index = self._check_index_of_current_looped_base_element(looped_base_reference)
        if loop_index not in self.current_subworkspace:
            self.current_subworkspace[loop_index] = {}
            logger.debug(f"[Quantifier.store_new_base_element] Initialized new entry at loop_index: {loop_index}")
        self.current_subworkspace[loop_index][self.loop_base_concept_name] = looped_base_reference
        logger.debug(f"[Quantifier.store_new_base_element] Stored at loop_index: {loop_index}")
        return loop_index


    def store_new_in_loop_element(self, looped_base_reference: Reference, looped_concept_name: str, looped_concept_reference: Reference) -> int:
        """
        Store a new in-loop element reference under a concept name.
        
        Args:
            looped_base_reference: Base reference to associate with
            looped_concept_name (str): Concept name to store under
            looped_concept_reference: Reference to store
            
        Returns:
            int: Loop index where element was stored
            
        Raises:
            ValueError: If base reference not found in subworkspace
        """
        logger.debug(f"[Quantifier.store_new_in_loop_element] Storing in-loop element: base tensor={getattr(looped_base_reference, 'tensor', None)}, concept_name: {looped_concept_name}, concept_reference.tensor={getattr(looped_concept_reference, 'tensor', None)}")
        loop_index = self._check_index_of_current_looped_base_element(looped_base_reference)
        if loop_index not in self.current_subworkspace:
            logger.error(f"[Quantifier.store_new_in_loop_element] Base reference not found in subworkspace for loop_index: {loop_index}")
            raise ValueError(f"The {looped_base_reference} is not in the current_subworkspace")
        self.current_subworkspace[loop_index][looped_concept_name] = looped_concept_reference
        logger.debug(f"[Quantifier.store_new_in_loop_element] Stored at loop_index: {loop_index}")
        return loop_index


    def retireve_next_base_element(self, to_loop_element_reference: Reference, current_loop_base_element: Optional[Reference] = None) -> Tuple[Optional[Reference], Optional[int]]:
        """
        Retrieve the next unprocessed base element from a reference.
        
        Skips elements matching current_loop_base_element and those already in workspace.
        
        Args:
            to_loop_element_reference: Reference containing elements
            current_loop_base_element: Current element to skip (optional)
            
        Returns:
            tuple: (element_reference, loop_index) or (None, None) if no elements left
        """
        logger.debug(f"[Quantifier.retireve_next_base_element] START: to_loop_element_reference.tensor={getattr(to_loop_element_reference, 'tensor', None)}, type={type(to_loop_element_reference)}, current_loop_base_element.tensor={getattr(current_loop_base_element, 'tensor', None) if current_loop_base_element else None}")
        logger.debug(f"[Quantifier.retireve_next_base_element] current_subworkspace keys: {list(self.current_subworkspace.keys())}")
        current_loop_index = 0
        max_iterations = 1000
        while True:
            logger.debug(f"[Quantifier.retireve_next_base_element] Loop index: {current_loop_index}")
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            logger.debug(f"[Quantifier.retireve_next_base_element] current_to_loop_element_reference.tensor: {getattr(current_to_loop_element_reference, 'tensor', None)}")
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            logger.debug(f"[Quantifier.retireve_next_base_element] elements: {elements}")
            if all(e is None or e == "@#SKIP#@" for e in elements):
                logger.debug(f"[Quantifier.retireve_next_base_element] All elements are None or SKIP at index {current_loop_index}, breaking loop.")
                break
            if current_loop_base_element is not None:
                try:
                    current_tensor = getattr(current_to_loop_element_reference, 'tensor', None)
                    base_tensor = getattr(current_loop_base_element, 'tensor', None)
                    logger.debug(f"[Quantifier.retireve_next_base_element] Comparing current_tensor: {current_tensor} with base_tensor: {base_tensor}")
                    if current_tensor == base_tensor:
                        logger.debug(f"[Quantifier.retireve_next_base_element] current_tensor matches base_tensor, incrementing index.")
                        current_loop_index += 1
                        continue
                except Exception as e:
                    logger.error(f"[Quantifier.retireve_next_base_element] Error comparing tensors: {e}")
            found_in_workspace = False
            for loop_index in self.current_subworkspace.keys():
                logger.debug(f"[Quantifier.retireve_next_base_element] Checking workspace at loop_index {loop_index}")
                if self.loop_base_concept_name in self.current_subworkspace[loop_index].keys():
                    workspace_ref = self.current_subworkspace[loop_index][self.loop_base_concept_name]
                    workspace_tensor = getattr(workspace_ref, 'tensor', None)
                    logger.debug(f"[Quantifier.retireve_next_base_element] Workspace tensor: {workspace_tensor}")
                    if current_to_loop_element_reference.tensor == workspace_tensor:
                        logger.debug(f"[Quantifier.retireve_next_base_element] Found tensor in workspace at index {loop_index}, incrementing current_loop_index.")
                        current_loop_index += 1
                        found_in_workspace = True
                        break
            if found_in_workspace:
                continue
            logger.debug(f"[Quantifier.retireve_next_base_element] Returning element at index {current_loop_index}")
            return current_to_loop_element_reference, current_loop_index
            if current_loop_index > max_iterations:
                logger.error("[Quantifier.retireve_next_base_element] Exceeded max iterations, stopping to avoid infinite loop.")
                break
        logger.debug(f"[Quantifier.retireve_next_base_element] END: returning None, None")
        return current_to_loop_element_reference, current_loop_index



    def check_all_base_elements_looped(self, to_loop_element_reference: Reference, in_loop_element_name: Optional[str] = None) -> bool:
        """
        Check if all elements in a reference have been processed.
        
        Args:
            to_loop_element_reference: Reference containing elements to check
            in_loop_element_name (str, optional): Additional concept to check for
            
        Returns:
            bool: True if all elements processed (and concept exists if specified)
        """
        logger.debug(f"[Quantifier.check_all_base_elements_looped] Checking all elements in tensor: {getattr(to_loop_element_reference, 'tensor', None)}, in_loop_element_name: {in_loop_element_name}")
        current_loop_index = 0
        while True:
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            logger.debug(f"[Quantifier.check_all_base_elements_looped] elements at index {current_loop_index}: {elements}")
            if all(e is None or e == "@#SKIP#@" for e in elements):
                logger.debug(f"[Quantifier.check_all_base_elements_looped] All elements processed at index {current_loop_index}")
                current_loop_index += 1
                break
            element_found = False
            matching_loop_index = None
            for loop_index in self.current_subworkspace.keys():
                if (self.loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                    current_to_loop_element_reference.tensor == self.current_subworkspace[loop_index][self.loop_base_concept_name].tensor):
                    element_found = True
                    matching_loop_index = loop_index
                    logger.debug(f"[Quantifier.check_all_base_elements_looped] Found element at loop_index: {loop_index}")
                    break
            if not element_found:
                logger.debug(f"[Quantifier.check_all_base_elements_looped] Element not found at index {current_loop_index}, returning False")
                return False
            if in_loop_element_name is not None and matching_loop_index is not None:
                if in_loop_element_name not in self.current_subworkspace[matching_loop_index].keys():
                    logger.debug(f"[Quantifier.check_all_base_elements_looped] In-loop element '{in_loop_element_name}' not found in loop index {matching_loop_index}")
                    return False
            current_loop_index += 1
        logger.debug(f"[Quantifier.check_all_base_elements_looped] All elements found and processed.")
        return True

    def combine_all_looped_elements_by_concept(self, to_loop_element_reference: Reference, concept_name: str) -> Optional[Reference]:
        """
        Combine references for a concept across all looped elements.
        
        Args:
            to_loop_element_reference: Reference containing elements to loop over
            concept_name (str): Concept name to combine
        
        Returns:
            Reference: Combined reference of all elements for the concept
                    or None if no references found
        """
        logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] START: concept_name={concept_name}, to_loop_element_reference.tensor={getattr(to_loop_element_reference, 'tensor', None)}")
        current_loop_index = 0
        all_concept_references = []
        while True:
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Loop index: {current_loop_index}")
            get_element_function = lambda x: self._get_list_at_index(x, current_loop_index)
            current_to_loop_element_reference = element_action(get_element_function, [to_loop_element_reference.copy()])
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] current_to_loop_element_reference.tensor: {getattr(current_to_loop_element_reference, 'tensor', None)}")
            elements = self._flatten_list(current_to_loop_element_reference.tensor.copy())
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] elements at index {current_loop_index}: {elements}")
            if all(e is None or e == "@#SKIP#@" for e in elements):
                logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] End of elements at index {current_loop_index}")
                current_loop_index += 1
                break
            matching_loop_index = None
            for loop_index in self.current_subworkspace.keys():
                logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Checking subworkspace loop_index {loop_index}")
                if (self.loop_base_concept_name in self.current_subworkspace[loop_index].keys() and 
                    current_to_loop_element_reference.tensor == self.current_subworkspace[loop_index][self.loop_base_concept_name].tensor):
                    matching_loop_index = loop_index
                    logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Found matching loop_index {matching_loop_index} for element {getattr(current_to_loop_element_reference, 'tensor', None)}")
                    break
            if matching_loop_index is not None and concept_name in self.current_subworkspace[matching_loop_index].keys():
                concept_reference = self.current_subworkspace[matching_loop_index][concept_name]
                all_concept_references.append(concept_reference)
                logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Added concept reference for index {matching_loop_index}: {getattr(concept_reference, 'tensor', None)} with axes {getattr(concept_reference, 'axes', None)}")
            else:
                logger.warning(f"[Quantifier.combine_all_looped_elements_by_concept] Concept '{concept_name}' not found for loop index {matching_loop_index}")
            current_loop_index += 1
        logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Collected {len(all_concept_references)} references for concept '{concept_name}'")
        if all_concept_references:
            combined_reference = cross_product(all_concept_references)
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] Combined reference tensor: {getattr(combined_reference, 'tensor', None)}, axes: {getattr(combined_reference, 'axes', None)}")
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] END: returning combined reference")
            return combined_reference
        else:
            logger.warning(f"[Quantifier.combine_all_looped_elements_by_concept] No references found for concept '{concept_name}'")
            logger.debug(f"[Quantifier.combine_all_looped_elements_by_concept] END: returning None")
            return None

    def retrieve_next_in_loop_element(self, concept_name: str, mode: str = 'carry_over', current_loop_index: int = 0, carry_index: int = 0) -> Reference:
        """
        Retrieve the next in-loop element for a concept.
        
        Args:
            concept_name (str): Concept name to retrieve
            mode (str): Retrieval mode ('carry_over' only currently supported)
            current_loop_index (int): Current loop index
            carry_index (int): Carry offset index
            
        Returns:
            Reference: Retrieved element reference
        """
        logger.debug(f"[Quantifier.retrieve_next_in_loop_element] concept_name: {concept_name}, mode: {mode}, current_loop_index: {current_loop_index}, carry_index: {carry_index}")
        if mode == 'carry_over':
            if current_loop_index > carry_index:
                concept_reference = self.current_subworkspace[current_loop_index - carry_index][concept_name]
                logger.debug(f"[Quantifier.retrieve_next_in_loop_element] Retrieved concept_reference.tensor: {getattr(concept_reference, 'tensor', None)}")
            else:
                concept_reference = Reference(initial_value=None, axes=None, shape=None)
                logger.debug(f"[Quantifier.retrieve_next_in_loop_element] Returning empty Reference (None)")
        return concept_reference

    def _log_current_subworkspace_tensors(self) -> None:
        """
        Log the current state of the subworkspace.
        
        Shows for each loop index: concept names and their reference tensors.
        """
        msg = "[Quantifier._log_current_subworkspace_tensors] current_subworkspace:"
        for loop_index, concept_dict in self.current_subworkspace.items():
            msg += f"\n  loop_index={loop_index}:"
            for concept_name, ref in concept_dict.items():
                tensor = getattr(ref, 'tensor', None)
                msg += f"  {concept_name}: tensor={tensor};"
        logger.debug(msg)

# IWC
def input_working_configurations(value_concepts: List[Concept], function_concept: Concept, 
                                concept_to_infer: Concept, all_working_configuration: dict):
    """
    Step 1: Input Working Configuration (IWC)
    
    Initializes the working configuration for the inference process.
    
    Args:
        value_concepts: List of value concepts
        function_concept: Function concept being applied
        concept_to_infer: Concept being inferred
        all_working_configuration: Complete working configuration dictionary
        
    Returns:
        dict: Initialized working configuration
    """
    logger.debug("[IWC] Executing input working configurations for quantification")
    logger.debug(f"[IWC] Value concepts: {[concept.name for concept in value_concepts]}")
    logger.debug(f"[IWC] Function concept: {function_concept.name}")
    logger.debug(f"[IWC] Concept to infer: {concept_to_infer.name}")
    
    # TODO: Implement input working configuration logic
    return all_working_configuration

#OWC
def output_working_configurations(working_configuration, function_concept, workspace, loop_base_concept_name, to_loop_elements, concept_to_infer):
    """
    Step 9: Output Working Configuration (OWC)
    
    Checks if all elements have been processed and updates the working configuration's completion status.
    
    Args:
        working_configuration: Current working configuration
        function_concept: Function concept being applied
        workspace: Current workspace state
        loop_base_concept_name: Name of loop base concept
        to_loop_elements: Elements to process from GP step
        concept_to_infer: Concept being inferred
        
    Returns:
        dict: Updated working configuration
    """
    logger.debug("[OWC] Executing output working configurations for quantification")
    logger.debug(f"[OWC] Function concept: {function_concept.name}")
    
    logger.debug("Executing status check for quantification")
    logger.debug(f"[OWC] To loop elements: {to_loop_elements}")
    logger.debug(f"[OWC] Concept to infer: {concept_to_infer.name}")

    if concept_to_infer.reference is None:
        working_configuration[function_concept.name]["completion_status"] = False
        logger.debug(f"[OWC] Completion status: {working_configuration[function_concept.name]['completion_status']}")
        return working_configuration
    
    processor = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    status = processor.check_all_base_elements_looped(to_loop_elements, concept_to_infer.name)
    working_configuration[function_concept.name]["completion_status"] = status
    logger.debug(f"[OWC] Completion status: {status}")
    
    return working_configuration


#FAP
def formal_actuator_perception(function_concept, value_concepts):
    """
    Step 2: Formal Actuator Perception (FAP)
    
    Parses the quantification normcode expression to extract:
    - Loop base concept
    - View axis
    - Concept to infer
    
    Prepares a function for grouping/combining references.
    
    Args:
        function_concept: Concept containing the normcode expression
        value_concepts: List of value concepts
        
    Returns:
        tuple: (formal_actuator_function, parsed_normcode_quantification)
    """
    logger.debug(f"[FAP] Executing FAP step with function concept: {function_concept.name}")

    parsed_normcode_quantification = _parse_normcode_quantification(function_concept.name)
    logger.debug(f"[FAP] Parsed normcode quantification: {parsed_normcode_quantification}")

    if value_concepts is None:
        value_concepts = []

    # Filter value concepts based on ViewAxis (similar to SliceAxis in grouping)
    value_concepts = [c for c in value_concepts if c.name in parsed_normcode_quantification["ViewAxis"]]
    logger.debug(f"[FAP] Value concepts: {[c.name for c in value_concepts]}")

    value_axes = [c.reference.axes for c in value_concepts]
    logger.debug(f"[FAP] Value axes: {value_axes}")

    grouper = Grouper()
    # For quantification, we always use or_across pattern
    quantification_actuated = lambda x: grouper.or_across(
        x, 
        slice_axes=value_axes,
    )

    return quantification_actuated, parsed_normcode_quantification

#GP
def group_perception(formal_actuator_function, value_concepts):
    """
    Step 3: Group Perception (GP)
    
    Generates the ordered list of elements to loop over based on the view axis.
    
    Args:
        formal_actuator_function: Function from FAP step
        value_concepts: List of value concepts
        
    Returns:
        Reference: Ordered list of elements to process (_toLoopElement_)
    """
    logger.debug(f"[GP] Executing GP step with formal actuator function: {formal_actuator_function}")

    perception_references = [c.reference for c in value_concepts]
    logger.debug(f"[GP] Perception references: {[c.name for c in value_concepts]}")

    new_perception_references = formal_actuator_function(perception_references)
    
    logger.debug(f"[GP] New perception references: {new_perception_references.tensor}, axes: {new_perception_references.axes}, shape: {new_perception_references.shape}")

    return new_perception_references


#PTA
def perception_tool_actuation(parsed_normcode_quantification, workspace, next_current_loop_base_element:Reference,
                          current_loop_base_element:Reference, concept_to_infer_name:str, current_loop_element:Reference, context_concepts:list[Concept],
                          is_new:bool) -> List[Concept]:
    """
    Step 6: Perception Tool Actuation (PTA)
    
    Updates workspace and context concepts:
    1. If current element is new, updates workspace with current loop base and concept to infer
    2. Updates context concepts for next iteration
    
    Args:
        parsed_normcode_quantification: Parsed normcode from FAP
        workspace: Current workspace state
        next_current_loop_base_element: Next element to process
        current_loop_base_element: Current element being processed
        concept_to_infer_name: Name of concept being inferred
        current_loop_element: Current value for concept to infer
        context_concepts: List of context concepts
        is_new: Whether current element is new
        
    Returns:
        List[Concept]: Updated context concepts
    """

    logger.debug(f"current_workspace: {workspace}")
    logger.debug(f"is_new: {is_new}")

    loop_base_concept_name = parsed_normcode_quantification['LoopBaseConcept']

    if is_new:
        quantifier = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
        quantifier.store_new_base_element(current_loop_base_element)
        quantifier.store_new_in_loop_element(current_loop_base_element, concept_to_infer_name, current_loop_element)
        logger.debug(f"[PTA] Current loop base element: {current_loop_base_element.tensor}, axes: {current_loop_base_element.axes}, shape: {current_loop_base_element.shape}")
        logger.debug(f"[PTA] Current loop element: {current_loop_element}")

    # TODO: This is a temporary fix to get the current loop base concept name.
    current_loop_base_concept_name = parsed_normcode_quantification['LoopBaseConcept'] + '*'

    logger.debug(f"[PTA] Parsed normcode quantification: {parsed_normcode_quantification}")
    logger.debug(f"[PTA] Context concepts: {[c.name for c in context_concepts]}")
    logger.debug(f"[PTA] Current loop base concept name: {current_loop_base_concept_name}")
    
    updated_context_concepts = []
    for context_concept in context_concepts:
        if parsed_normcode_quantification["InLoopConcept"] is not None:
            if context_concept.name in parsed_normcode_quantification["InLoopConcept"]:
                if is_new:
                    quantifier.store_new_in_loop_element(current_loop_base_element, context_concept.name, context_concept.reference) # type: ignore
                    logger.debug(f"[PTA] Current loop base element: {current_loop_base_element.tensor}, axes: {current_loop_base_element.axes}, shape: {current_loop_base_element.shape}")
                    current_loop_index = parsed_normcode_quantification["InLoopConcept"][context_concept.name]
                    current_in_loop_concept_reference = quantifier.retrieve_next_in_loop_element(context_concept.name, current_loop_index)
                    context_concept.reference = current_in_loop_concept_reference
                    logger.debug(f"[PTA] Current in loop concept reference: {current_in_loop_concept_reference.tensor}, axes: {current_in_loop_concept_reference.axes}, shape: {current_in_loop_concept_reference.shape}")
        if context_concept.name == current_loop_base_concept_name:
            logger.debug(f"[PTA] Next current loop base concept element: {next_current_loop_base_element.tensor}, axes: {next_current_loop_base_element.axes}, shape: {next_current_loop_base_element.shape}")
            context_concept.reference = next_current_loop_base_element.copy()
            logger.debug(f"[PTA] Context concept: {context_concept.name}, reference: {context_concept.reference.tensor}, axes: {context_concept.reference.axes}, shape: {context_concept.reference.shape}")
        updated_context_concepts.append(context_concept)

    logger.debug(f"[PTA] Updated workspace: {workspace}")
    if is_new:
        quantifier._log_current_subworkspace_tensors()
    return updated_context_concepts


# CVP
def context_value_perception(context_concepts, parsed_normcode_quantification, workspace, to_loop_elements):
    """
    Step 4: Context Value Perception (CVP)
    
    Determines:
    - Current element in the loop (_currentLoopBaseConcept_)
    - Whether the element is new
    - Next element to process
    
    Args:
        context_concepts: List of context concepts
        parsed_normcode_quantification: Parsed normcode from FAP
        workspace: Current workspace state
        to_loop_elements: Elements to process from GP step
        
    Returns:
        tuple: (current_loop_element, is_new, next_current_loop_base_element)
    """
    logger.debug("[CVP] START context_value_perception")
    logger.debug(f"[CVP] context_concepts: {[c.name for c in context_concepts]}")
    logger.debug(f"[CVP] parsed_normcode_quantification: {parsed_normcode_quantification}")
    logger.debug(f"[CVP] workspace keys: {list(workspace.keys())}")
    logger.debug(f"[CVP] to_loop_elements.tensor: {getattr(to_loop_elements, 'tensor', None)}")
    in_loop_concept_name = parsed_normcode_quantification['LoopBaseConcept'] + '*'  # e.g., '{digit position}*'
    current_loop_base_concept = None
    for c in context_concepts:
        if c.name == in_loop_concept_name:
            current_loop_base_concept = c
            break
    if current_loop_base_concept is None:
        logger.warning(f"[CVP] No context concept found with name {in_loop_concept_name}")
        return None, False, None
    logger.debug(f"[CVP] current_loop_base_concept: {current_loop_base_concept.name}")
    quantifier = Quantifier(workspace=workspace, loop_base_concept_name=parsed_normcode_quantification['LoopBaseConcept'])
    current_element = None
    if current_loop_base_concept.reference:
        current_element = current_loop_base_concept.reference
    logger.debug(f"[CVP] current_element: {current_element}, type: {type(current_element)}")
    next_current_loop_base_element, idx = quantifier.retireve_next_base_element(to_loop_elements, current_loop_base_element=current_element)
    logger.debug(f'[CVP] next_current_loop_base_element: {getattr(next_current_loop_base_element, "tensor", None)}, index: {idx}')
    if current_element and quantifier._check_new_base_element_by_looped_base_element(current_element, current_loop_base_concept.name):
        logger.debug("[CVP] New element detected in context value perception")
        new_element = True
    else:
        logger.debug("[CVP] Element is not new or no element found")
        current_element = next_current_loop_base_element
        new_element = False
    logger.debug(f"[CVP] END context_value_perception: next_current_loop_base_element: {getattr(next_current_loop_base_element, 'tensor', None)}, new_element: {new_element}")
    return current_element, new_element, next_current_loop_base_element


# AVP
def actuator_value_perception(function_concept):
    """
    Step 5: Actuator Value Perception (AVP)
    
    Loads the current value for the concept to infer.
    
    Args:
        function_concept: Function concept being applied
        
    Returns:
        Reference: Current value for the concept to infer (_currentConceptToInferElement_)
    """
    logger.debug("[AVP] Executing actuator value perception for quantification")
    logger.debug(f"[AVP] Function concept: {function_concept.name}")
    
    if function_concept.reference:
        logger.debug(f"[AVP] Function concept reference: {function_concept.reference.tensor}")
        return function_concept.reference
    
    logger.debug("[AVP] Function concept reference is None")
    return None

#GA
def grouping_actuation(workspace, to_loop_elements_reference, parsed_normcode_quantification, concept_to_infer, context_concepts: list[Concept], value_concepts: list[Concept]):
    """
    Step 7: Grouping Actuation (GA)
    
    Combines all processed elements for the concept to infer into a single reference.
    Also adjusts the axes of the combined reference:
        - Any axis named {concept_to_infer.name}_in_loop is renamed to {concept_to_infer.name}
        - The last axis (which is the loop axis) is renamed to {concept_to_infer.name}
    
    Args:
        workspace: Current workspace state
        to_loop_elements_reference: Elements to process from GP step
        parsed_normcode_quantification: Parsed normcode from FAP
        concept_to_infer: Concept being inferred
        
    Returns:
        Reference: Combined result reference
    """
    logger.debug("[GA] Executing grouping actuation for quantification")
    logger.debug(f"[GA] Concept to infer: {concept_to_infer.name}")
    logger.debug(f"[GA] To loop elements reference: {to_loop_elements_reference}")
    
    loop_base_concept_name = parsed_normcode_quantification['LoopBaseConcept']
    current_loop_base_concept_name = loop_base_concept_name + '*'
    logger.debug(f"[GA] Loop base concept name: {loop_base_concept_name}")

    processor = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    combined_reference = processor.combine_all_looped_elements_by_concept(to_loop_elements_reference, concept_to_infer.name)
    
    loop_base_concept_axis = [concept.context for concept in value_concepts if concept.name == loop_base_concept_name][0]
    logger.debug(f"[GA] Loop base concept axis: {loop_base_concept_axis}")
    current_loop_base_concept_axis = [concept.context for concept in context_concepts if concept.name == current_loop_base_concept_name][0]
    logger.debug(f"[GA] Current loop base concept axis: {current_loop_base_concept_axis}")


    # Adjust axes of combined reference
    if combined_reference:
        new_axes = combined_reference.axes.copy()
        new_axes[-1] = concept_to_infer.context
        # # make sure that current_loop_base_concept_axis in the old axis is changed to loop_base_concept_axis
        # new_axes[new_axes.index(current_loop_base_concept_axis)] = loop_base_concept_axis
        # logger.debug(f"[GA] New axis: {new_axes}")
        combined_reference.axes = new_axes
        logger.debug(f"[GA] Combined reference axes: {combined_reference.axes}")
        logger.debug(f"[GA] Combined reference tensor: {combined_reference.tensor}")

    return combined_reference



#RR
def return_reference(concept_to_infer_reference, concept_to_infer):
    """
    Step 8: Return Reference (RR)
    
    Sets the reference for the concept to infer to the combined result from GA.
    
    Args:
        concept_to_infer_reference: Combined reference from GA
        concept_to_infer: Concept being inferred
        
    Returns:
        Concept: Concept to infer with updated reference
    """
    logger.debug("[RR] Executing return reference for quantification")
    logger.debug(f"[RR] Concept to infer reference: {concept_to_infer_reference}")
    logger.debug(f"[RR] Concept to infer: {concept_to_infer.name}")
    
    # TODO: Implement return reference logic
    concept_to_infer.reference = concept_to_infer_reference

    return concept_to_infer
