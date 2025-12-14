from typing import Any, Dict, List, Optional
from string import Template
from copy import copy

from infra._core import Reference, cross_product, element_action


class Grouper:
    """
    A class that abstracts NormCode grouping patterns as functions of references.
    Provides methods for different grouping operations.
    """

    def __init__(self, skip_value="@#SKIP#@"):
        self.skip_value = skip_value

    def find_share_axes(self, references: List[Reference]) -> List[str]:
        if not references:
            return []
        shared_axes = set(references[0].axes)
        for ref in references[1:]:
            shared_axes.intersection_update(ref.axes)
        return list(shared_axes)

    def flatten_element(self, reference: Reference) -> Reference:
        def flatten_all_list(nested_list):
            if not isinstance(nested_list, list):
                return [nested_list]
            return sum((flatten_all_list(item) for item in nested_list), [])

        return element_action(flatten_all_list, [reference])

    def annotate_element(self, reference: Reference, annotation_list: List[str]) -> Reference:
        def annotate_list(lst: List[Any]) -> Dict[str, Any] | str:
            if len(lst) != len(annotation_list):
                return self.skip_value

            annotation_dict = {}
            for i, annotation in enumerate(annotation_list):
                value = lst[i]
                if isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
                    value = value[0]
                annotation_dict[annotation] = value
            return annotation_dict

        return element_action(annotate_list, [reference])

    def create_unified_element_actuation(self, template: Template, annotation_list: Optional[List[str]] = None):
        def element_actuation(element: Any) -> str:
            return_string = ""
            elements = element if isinstance(element, list) else [element]

            for one_element in elements:
                input_dict = {}
                if annotation_list is not None:
                    # Annotated case
                    for i, annotation in enumerate(annotation_list):
                        input_value = one_element.get(annotation, self.skip_value)
                        input_dict[f"input{i+1}"] = str(input_value)
                else:
                    # Non-annotated case
                    if isinstance(one_element, list):
                        format_string = "; ".join(map(str, one_element))
                        input_dict = {"input1": format_string}
                    else:
                        input_dict = {"input1": str(one_element)}

                template_copy = copy(template)
                result_string = template_copy.safe_substitute(**input_dict) + " \n"
                return_string += result_string

            return return_string

        return element_actuation

    def and_in(self, references: List[Reference], annotation_list: List[str], by_axes: Optional[List[str]] = None, template: Optional[Template] = None) -> Reference:
        shared_axes = self.find_share_axes(references)
        sliced_refs = [ref.slice(*shared_axes) for ref in references]

        result = cross_product(sliced_refs)
        result = self.annotate_element(result, annotation_list)

        if by_axes is not None:
            preserve_axes = [axis for axis in result.axes if axis not in by_axes]
            result = result.slice(*preserve_axes)

        if template:
            element_actuation = self.create_unified_element_actuation(template, annotation_list)
            result = element_action(element_actuation, [result])

        return result

    def or_across(
        self, 
        references: List[Reference], 
        by_axes: Optional[List] = None,  # List[str] (shared) or List[List[str]] (per-ref)
        template: Optional[Template] = None,
        create_axis: Optional[str] = None
    ) -> Reference:
        """
        Group references into a flat collection.
        
        Args:
            references: List of references to group
            by_axes: Either:
                - List[str]: Shared axes to collapse (legacy behavior)
                - List[List[str]]: Per-reference axes to collapse
            template: Optional template for formatting
            create_axis: Name for the resulting axis dimension (enables per-ref mode)
        
        When create_axis is specified with per-ref by_axes:
            1. For each reference, collapse its specified axes (using slice + _get_leaves)
            2. Concatenate all extracted elements
            3. Wrap in create_axis dimension
        
        Otherwise uses legacy cross_product + flatten behavior.
        """
        if not references:
            axis_name = create_axis or "_none_axis"
            return Reference(axes=[axis_name], shape=(0,))
        
        # Normalize by_axes format for backward compatibility
        # If by_axes is a flat list ["axis1", "axis2"], convert to per-ref format
        # by broadcasting to all references: [["axis1", "axis2"], ["axis1", "axis2"], ...]
        normalized_by_axes = by_axes
        if by_axes is not None and len(by_axes) > 0:
            if not isinstance(by_axes[0], list):
                # Flat list (legacy format) - broadcast to all references if create_axis specified
                if create_axis is not None:
                    normalized_by_axes = [by_axes for _ in references]
                # else: leave as flat list for legacy behavior
        
        # Check if per-reference mode
        is_per_ref_mode = (
            create_axis is not None and 
            normalized_by_axes is not None and 
            len(normalized_by_axes) > 0 and 
            isinstance(normalized_by_axes[0], list)
        )
        
        if is_per_ref_mode:
            # Per-reference collapse + concatenate mode
            all_elements = []
            
            for i, ref in enumerate(references):
                # Get axes to collapse for this reference
                axes_to_collapse = normalized_by_axes[i] if i < len(normalized_by_axes) else list(ref.axes)
                
                # Determine which axes to PRESERVE (not collapse)
                preserve_axes = [ax for ax in ref.axes if ax not in axes_to_collapse]
                
                if preserve_axes:
                    # Partial collapse: slice to preserve axes, then extract leaves
                    sliced = ref.slice(*preserve_axes)
                    elements = list(sliced._get_leaves())
                else:
                    # Full collapse: extract all leaves directly
                    elements = list(ref._get_leaves())
                
                all_elements.extend(elements)
            
            # Create result with new axis
            result = Reference(
                axes=[create_axis],
                shape=(len(all_elements),),
                initial_value=None,
                skip_value=self.skip_value
            )._replace_data(all_elements)
        
        else:
            # Legacy behavior: cross_product + flatten
            shared_axes = self.find_share_axes(references)
            sliced_refs = [ref.slice(*shared_axes) for ref in references]

            result = cross_product(sliced_refs)

            if by_axes is not None:
                preserve_axes = [axis for axis in result.axes if axis not in by_axes]
                result = result.slice(*preserve_axes)

            result = self.flatten_element(result)

        if template:
            element_actuation = self.create_unified_element_actuation(template, None)
            result = element_action(element_actuation, [result])

        return result 