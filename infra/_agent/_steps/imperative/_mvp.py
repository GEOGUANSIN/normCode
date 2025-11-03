from typing import Any, Dict, List
import logging

from infra._states._imperative_states import States
from infra._core import Reference, cross_product, element_action


def _apply_selector(ref: Reference, selector: Dict[str, Any]) -> Reference:
    """Applies a selector to a reference to extract a specific value."""
    index = selector.get("index")
    key = selector.get("key")

    def selector_action(element):
        import ast

        processed_element = element
        if isinstance(element, str) and element.startswith("%"):
            open_paren_index = element.find("(")
            close_paren_index = element.rfind(")")
            if open_paren_index > 0 and close_paren_index == len(element) - 1:
                content = element[open_paren_index + 1 : close_paren_index]
                try:
                    processed_element = ast.literal_eval(content)
                except (ValueError, SyntaxError):
                    processed_element = content
        
        selected = processed_element
        if index is not None and isinstance(selected, list) and len(selected) > index:
            selected = selected[index]
        
        if key is not None and isinstance(selected, dict):
            selected = selected.get(key)
            
        return selected

    # We need to handle nested lists, the tensor might be like [[{...}, {...}]]
    def nested_selector_action(element):
        if isinstance(element, list):
            return [selector_action(item) for item in element]
        return selector_action(element)

    return element_action(nested_selector_action, [ref])


def memory_value_perception(states: States) -> States:
    """Order and cross-product value references based on working_configuration."""

    ir_func_record = next((f for f in states.function if f.step_name == "IR"), None)
    func_name = ir_func_record.concept.name if ir_func_record and ir_func_record.concept else ""

    value_order = states.value_order
    value_selectors = states.value_selectors or {}

    name_to_ref: Dict[str, Reference] = {
        v.concept.name: v.reference
        for v in states.values
        if v.step_name == "IR" and v.concept and v.reference
    }

    # Apply selectors before ordering
    for name, selector in value_selectors.items():
        if name in name_to_ref:
            logging.debug(f"Applying selector to '{name}': {selector}")
            name_to_ref[name] = _apply_selector(name_to_ref[name], selector)

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
        # Step 1: Strip wrappers like %() from each reference before cross-product.
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

        # Step 2: Cross product to get lists of values.
        crossed_ref = cross_product(stripped_refs)

        # Step 3: Use element_action to convert lists to dicts with generic keys.
        # The keys "input_1", "input_2", etc. match the prompt templates.
        def list_to_dict(values_list: List[Any]) -> Dict[str, Any]:
            """Creates a dict with keys like 'input_1', 'input_2'."""
            return {f"input_{i + 1}": val for i, val in enumerate(values_list)}

        dict_ref = element_action(list_to_dict, [crossed_ref])
        states.set_reference("values", "MVP", dict_ref)

    states.set_current_step("MVP")
    logging.debug(f"MVP completed. Values state after cross-product and dict conversion: {states.values}")
    return states 