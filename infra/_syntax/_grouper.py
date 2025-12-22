from typing import Any, Dict, List, Optional, Tuple
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

    # =========================================================================
    # SHARED HELPER METHODS FOR CONSISTENT GROUPING BEHAVIOR
    # =========================================================================

    def _normalize_by_axes(
        self, 
        by_axes: Optional[List], 
        references: List[Reference]
    ) -> Tuple[Optional[List[List[str]]], bool]:
        """
        Normalize by_axes to per-reference format.
        
        Returns:
            (normalized_by_axes, is_per_ref_mode)
        """
        if by_axes is None or len(by_axes) == 0:
            return None, False
        
        # Check if already per-ref format
        if isinstance(by_axes[0], list):
            return by_axes, True
        
        # Flat list - broadcast to all references
        normalized = [by_axes for _ in references]
        return normalized, True

    def _extract_elements_from_ref(
        self,
        ref: Reference,
        specified_axes: List[str],
        annotate_with: Optional[str] = None
    ) -> Tuple[List[Any], Optional[List[str]], bool]:
        """
        Extract elements from a reference based on specified axes to collapse.
        
        Args:
            ref: The reference to extract from
            specified_axes: Axes that should be collapsed
            annotate_with: If provided, wrap each element in {annotate_with: elem}
        
        Returns:
            (elements, preserved_axes, is_stack_mode)
            - elements: List of extracted elements
            - preserved_axes: Axes that were preserved (for stack mode)
            - is_stack_mode: True if tensor structure was kept intact
        """
        # Filter to only axes that actually exist in ref
        axes_to_collapse = [ax for ax in specified_axes if ax in ref.axes]
        
        # Determine which axes to PRESERVE (not collapse)
        preserve_axes = [ax for ax in ref.axes if ax not in axes_to_collapse]
        
        elements = []
        is_stack_mode = False
        
        if not axes_to_collapse and preserve_axes:
            # STACK MODE: No collapsing (specified axes don't match actual axes)
            # Keep tensor structure intact, keep SKIPs for index consistency
            tensor_data = ref.tensor
            if annotate_with:
                elements.append({annotate_with: tensor_data})
            else:
                elements.append(tensor_data)
            is_stack_mode = True
            return elements, preserve_axes, is_stack_mode
        
        elif preserve_axes:
            # Partial collapse: slice to preserve axes, then extract leaves
            sliced = ref.slice(*preserve_axes)
            raw_elements = list(sliced._get_leaves())
        else:
            # Full collapse: extract all leaves directly
            raw_elements = list(ref._get_leaves())
        
        # Filter SKIPs when axes are stripped (collapse mode)
        for elem in raw_elements:
            if elem != self.skip_value:
                if annotate_with:
                    elements.append({annotate_with: elem})
                else:
                    elements.append(elem)
        
        return elements, preserve_axes if is_stack_mode else None, is_stack_mode

    def _build_result_reference(
        self,
        elements: List[Any],
        create_axis: Optional[str],
        preserved_axes: Optional[List[str]] = None
    ) -> Reference:
        """
        Build the result reference based on collected elements and axis configuration.
        
        Args:
            elements: List of elements to include in result
            create_axis: Explicit axis name, or None for _none_axis behavior
            preserved_axes: Axes preserved from stack mode (if any)
        
        Returns:
            Reference with appropriate structure
        """
        if create_axis is not None:
            # Explicit axis: create N elements along that axis
            if preserved_axes:
                # Stack mode: result has [create_axis] + preserved_axes
                result_axes = [create_axis] + preserved_axes
                # Calculate shape based on first element structure
                if elements and isinstance(list(elements[0].values())[0] if isinstance(elements[0], dict) else elements[0], list):
                    first_val = list(elements[0].values())[0] if isinstance(elements[0], dict) else elements[0]
                    result_shape = (len(elements),) + tuple(
                        len(first_val) if isinstance(first_val, list) else 1
                        for _ in preserved_axes
                    )
                else:
                    result_shape = (len(elements),) + (1,) * len(preserved_axes)
                return Reference(
                    axes=result_axes,
                    shape=result_shape,
                    initial_value=None,
                    skip_value=self.skip_value
                )._replace_data(elements)
            else:
                # 1D result with create_axis
                return Reference(
                    axes=[create_axis],
                    shape=(len(elements),),
                    initial_value=None,
                    skip_value=self.skip_value
                )._replace_data(elements)
        else:
            # No explicit axis (_none_axis): wrap all elements into a single element
            # Shape (1,) where the element is the list of all elements
            return Reference(
                axes=["_none_axis"],
                shape=(1,),
                initial_value=None,
                skip_value=self.skip_value
            )._replace_data([elements])

    # =========================================================================
    # MAIN GROUPING METHODS
    # =========================================================================

    def and_in(
        self, 
        references: List[Reference], 
        annotation_list: List[str], 
        by_axes: Optional[List] = None,  # List[str] (shared) or List[List[str]] (per-ref)
        template: Optional[Template] = None,
        create_axis: Optional[str] = None
    ) -> Reference:
        """
        Group references into a labeled relation (dict-like structure).
        
        Args:
            references: List of references to group
            annotation_list: Names to use as keys in the dict
            by_axes: Either:
                - List[str]: Shared axes to collapse (legacy behavior)
                - List[List[str]]: Per-reference axes to collapse
            template: Optional template for formatting
            create_axis: Name for the resulting axis dimension
                - If provided: creates N elements along that axis
                - If None: creates single element containing list of all (_none_axis)
        """
        if not references:
            axis_name = create_axis or "_none_axis"
            return Reference(axes=[axis_name], shape=(0,))
        
        # Normalize by_axes format
        normalized_by_axes, is_per_ref_mode = self._normalize_by_axes(by_axes, references)
        
        if is_per_ref_mode:
            # Per-reference collapse + annotate mode
            all_elements = []
            preserved_axes_for_result = None
            
            for i, (ref, name) in enumerate(zip(references, annotation_list)):
                specified_axes = normalized_by_axes[i] if i < len(normalized_by_axes) else list(ref.axes)
                
                elements, preserved, is_stack = self._extract_elements_from_ref(
                    ref, specified_axes, annotate_with=name
                )
                all_elements.extend(elements)
                
                if is_stack and preserved_axes_for_result is None:
                    preserved_axes_for_result = preserved
            
            result = self._build_result_reference(all_elements, create_axis, preserved_axes_for_result)
        
        else:
            # Legacy behavior: cross_product + annotate + collapse
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
            create_axis: Name for the resulting axis dimension
                - If provided: creates N elements along that axis
                - If None: creates single element containing list of all (_none_axis)
        """
        if not references:
            axis_name = create_axis or "_none_axis"
            return Reference(axes=[axis_name], shape=(0,))
        
        # Normalize by_axes format
        normalized_by_axes, is_per_ref_mode = self._normalize_by_axes(by_axes, references)
        
        if is_per_ref_mode:
            # Per-reference collapse + concatenate mode
            all_elements = []
            preserved_axes_for_result = None
            
            for i, ref in enumerate(references):
                specified_axes = normalized_by_axes[i] if i < len(normalized_by_axes) else list(ref.axes)
                
                elements, preserved, is_stack = self._extract_elements_from_ref(
                    ref, specified_axes, annotate_with=None
                )
                all_elements.extend(elements)
                
                if is_stack and preserved_axes_for_result is None:
                    preserved_axes_for_result = preserved
            
            result = self._build_result_reference(all_elements, create_axis, preserved_axes_for_result)
        
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
