from _reference import Reference, cross_product, element_action
import _logger
from _logger import logger
from copy import copy

# Local helper to find references by step_name in a list of StepReference

def step(ref_list, name):
    return [r for r in ref_list if getattr(r, "step_name", None) == name]

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
    
    
    def and_in(self, references, annotation_list, by_axes=None, template=None, pop=True, slice_axes=None):
        """
        Implement the AND patterns: 
        - AND IN: [{old expression} and {new expression} in all {old expression}] (when by_axes provided)
        - AND ONLY: [{old expression} and {new expression}] (when by_axes is None)
        
        Args:
            references (list): List of Reference objects to combine
            annotation_list (list): List of annotation labels
            by_axes (list, optional): List of axes to group by (these axes are NOT preserved). 
                                       If None, no by-axis grouping is performed (AND ONLY pattern).
            template (Template, optional): Template for processing results
            
        Returns:
            Reference: Processed reference with annotations
        """
        # Backward compatibility with old parameter name
        if by_axes is None and slice_axes is not None:
            by_axes = slice_axes
        elif by_axes is not None and slice_axes is not None:
            raise ValueError("Provide only by_axes or slice_axes, not both")

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

        # Apply by-axes grouping if provided (AND IN pattern)
        if by_axes is not None and len(by_axes) > 0:
            if not isinstance(by_axes[0], list):
                by_axes = [by_axes]

            # Axes not listed in any by_axes groups should be preserved
            preserve_axes = [axis for axis in result.axes if not any(axis in sublist for sublist in by_axes)]
            
            by_axes_copy = by_axes.copy()  # Create a copy to avoid modifying the original
            if pop:
                # Pop the last element from each sublist
                for i in range(len(by_axes_copy)):
                    if by_axes_copy[i]:  # Check if sublist is not empty
                        by_axes_copy[i].pop()

            # Find axes that are present in all sublists (common grouping axes)
            axes_in_all_groups = [axis for axis in result.axes if all(axis in sublist for sublist in by_axes_copy)] if by_axes_copy[0] else []

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
    
    def or_across(self, references, by_axes=None, template=None, pop=True, slice_axes=None):
        """
        Implement the OR patterns:
        - OR ACROSS: [{old expression} or {new expression} across all {old expression}] (when by_axes provided)
        - OR ONLY: [{old expression} or {new expression}] (when by_axes is None)
        
        Args:
            references (list): List of Reference objects to combine
            by_axes (list, optional): List of axes to group by (these axes are NOT preserved).
                                       If None, no by-axis grouping is performed (OR ONLY pattern).
            template (Template, optional): Template for processing results
            
        Returns:
            Reference: Processed reference with flattened elements
        """
        # Backward compatibility with old parameter name
        if by_axes is None and slice_axes is not None:
            by_axes = slice_axes
        elif by_axes is not None and slice_axes is not None:
            raise ValueError("Provide only by_axes or slice_axes, not both")

        # Find shared axes
        shared_axes = self.find_share_axes(references)
        
        # Slice references to shared axes
        sliced_refs = [ref.slice(*shared_axes) for ref in references]
        
        # Perform cross product
        result = cross_product(sliced_refs)
        
        # Apply by-axes grouping if provided (OR ACROSS pattern)
        if by_axes is not None and len(by_axes) > 0:
            if not isinstance(by_axes[0], list):
                by_axes = [by_axes]
                
            # Axes not listed in any by_axes groups should be preserved
            preserve_axes = [axis for axis in result.axes if not any(axis in sublist for sublist in by_axes)]
            
            by_axes_copy = by_axes.copy()  # Create a copy to avoid modifying the original
            if pop:
                # Pop the last element from each sublist
                for i in range(len(by_axes_copy)):
                    if by_axes_copy[i]:  # Check if sublist is not empty
                        by_axes_copy[i].pop()

            # Find axes that are present in all sublists (common grouping axes)
            axes_in_all_groups = [axis for axis in result.axes if all(axis in sublist for sublist in by_axes_copy)] if by_axes_copy[0] else []

            final_slice_axes = preserve_axes + axes_in_all_groups
            result = result.slice(*final_slice_axes)
        
        # Flatten elements
        result = self.flatten_element(result)
        
        # Apply template if provided
        if template:
            element_actuation = self.create_unified_element_actuation(template, None)
            result = element_action(element_actuation, [result])
        
        return result
    
from _state_models import (
    AgentSequenceState, StepDescriptor, ReferenceInterpretationState,
    FunctionReference, ValuesReference, ContextReference, InferenceReference,
    ModelSpec, ToolSpec, ConceptInfo, StepReferenceAccessor
)


def grouping_references(states):

    st = StepReferenceAccessor

    context_concepts_references = st(states.context).reference
    value_concepts_references = st(states.values).reference
    value_concepts = st(states.values).concept

    by_axes = [c.axes for c in context_concepts_references]
    value_concept_names = [c.name for c in value_concepts]

    grouper = Grouper()
    if states.syntax.marker == "in":
        step(states.inference, "GA")[0].reference = grouper.and_in(
            value_concepts_references, 
            value_concept_names, 
            by_axes=by_axes,
        ).copy()
    elif states.syntax.marker == "across":
        step(states.inference, "GA")[0].reference = grouper.or_across(
            value_concepts_references, 
            by_axes=by_axes,
        ).copy()

    return states