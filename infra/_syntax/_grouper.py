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

    def and_in(self, references: List[Reference], annotation_list: List[str], by_axes: Optional[List[List[str]]] = None, template: Optional[Template] = None, pop: bool = True) -> Reference:
        shared_axes = self.find_share_axes(references)
        sliced_refs = [ref.slice(*shared_axes) for ref in references]

        result = cross_product(sliced_refs)
        result = self.annotate_element(result, annotation_list)

        if by_axes is not None and len(by_axes) > 0:
            preserve_axes = [axis for axis in result.axes if not any(axis in sublist for sublist in by_axes)]

            by_axes_copy = copy(by_axes)
            if pop:
                for i in range(len(by_axes_copy)):
                    if by_axes_copy[i]:
                        by_axes_copy[i].pop()

            axes_in_all_groups = [axis for axis in result.axes if all(axis in sublist for sublist in by_axes_copy)] if by_axes_copy and by_axes_copy[0] else []
            final_slice_axes = preserve_axes + axes_in_all_groups
            result = result.slice(*final_slice_axes)

        if template:
            element_actuation = self.create_unified_element_actuation(template, annotation_list)
            result = element_action(element_actuation, [result])

        return result

    def or_across(self, references: List[Reference], by_axes: Optional[List[List[str]]] = None, template: Optional[Template] = None, pop: bool = True) -> Reference:
        shared_axes = self.find_share_axes(references)
        sliced_refs = [ref.slice(*shared_axes) for ref in references]

        result = cross_product(sliced_refs)

        if by_axes is not None and len(by_axes) > 0:
            preserve_axes = [axis for axis in result.axes if not any(axis in sublist for sublist in by_axes)]

            by_axes_copy = copy(by_axes)
            if pop:
                for i in range(len(by_axes_copy)):
                    if by_axes_copy[i]:
                        by_axes_copy[i].pop()

            axes_in_all_groups = [axis for axis in result.axes if all(axis in sublist for sublist in by_axes_copy)] if by_axes_copy and by_axes_copy[0] else []
            final_slice_axes = preserve_axes + axes_in_all_groups
            result = result.slice(*final_slice_axes)

        result = self.flatten_element(result)

        if template:
            element_actuation = self.create_unified_element_actuation(template, None)
            result = element_action(element_actuation, [result])

        return result 