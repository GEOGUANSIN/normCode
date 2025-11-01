from typing import Any, Dict, List
import logging

from infra._states._imperative_states import States
from infra._core import Reference, cross_product, element_action


def memory_value_perception(states: States) -> States:
    """
    Order and extract value references for user input.
    For imperative_input, we extract the prompt text and any additional context.
    """
    value_order = states.value_order

    name_to_ref: Dict[str, Reference] = {
        v.concept.name: v.reference
        for v in states.values
        if v.step_name == "IR" and v.concept and v.reference
    }

    ordered_refs: List[Reference] = []
    ordered_names: List[str] = []
    if value_order:
        sorted_items = sorted(value_order.items(), key=lambda item: item[1])
        for name, _ in sorted_items:
            if name in name_to_ref:
                ordered_refs.append(name_to_ref[name])
                ordered_names.append(name)
    else:
        # Fallback if no order is specified
        for name, ref in name_to_ref.items():
            ordered_refs.append(ref)
            ordered_names.append(name)

    if ordered_refs:
        # Strip wrappers like %() from each reference before cross-product.
        def strip_wrapper(element: Any) -> Any:
            """
            Strips the '%...(...)' wrapper from strings in an element.
            If the element is a list or contains lists, it flattens the structure,
            processes each item, and joins them into a formatted string.
            """
            from typing import List

            flat_list: List[Any] = []

            def flatten(el: Any):
                if isinstance(el, list):
                    for item in el:
                        flatten(item)
                elif isinstance(el, dict):
                    for value in el.values():
                        flatten(value)
                else:
                    flat_list.append(el)

            flatten(element)

            stripped_list = []
            for item in flat_list:
                if isinstance(item, str) and item.startswith("%"):
                    open_paren_index = item.find("(")
                    close_paren_index = item.rfind(")")
                    if open_paren_index > 0 and close_paren_index == len(item) - 1:
                        stripped_list.append(item[open_paren_index + 1 : close_paren_index])
                    else:
                        stripped_list.append(item)
                else:
                    stripped_list.append(item)

            if not stripped_list:
                return ""
            if len(stripped_list) == 1:
                return str(stripped_list[0])
            if len(stripped_list) == 2:
                return f"{stripped_list[0]}, and {stripped_list[1]}"
            return ", ".join(map(str, stripped_list[:-1])) + f", and {stripped_list[-1]}"

        stripped_refs = [element_action(strip_wrapper, [ref]) for ref in ordered_refs]

        # Cross product to get lists of values.
        crossed_ref = cross_product(stripped_refs)

        # Convert lists to dicts. First value is assumed to be the prompt text.
        def list_to_dict(values_list: List[Any]) -> Dict[str, Any]:
            """
            Creates a dict with prompt_text and any additional inputs.
            For user input, the first value is typically the prompt/question.
            """
            output_dict = {}
            if values_list:
                # First value is the prompt/question
                output_dict["prompt_text"] = str(values_list[0]) if values_list else ""
                # Remaining values are additional context
                for i, input_val in enumerate(values_list[1:], start=1):
                    output_dict[f"context_{i}"] = input_val
            return output_dict

        dict_ref = element_action(list_to_dict, [crossed_ref])
        states.set_reference("values", "MVP", dict_ref)

    states.set_current_step("MVP")
    logging.debug(f"MVP completed. Values state after cross-product and dict conversion: {states.values}")
    return states
