from typing import Any, Dict, List
import logging

from infra._states._judgement_states import States
from infra._core import Reference, cross_product, element_action


def memory_value_perception(states: States) -> States:
    """Order and cross-product value references based on working_configuration."""

    ir_func_record = next((f for f in states.function if f.step_name == "IR"), None)
    func_name = ir_func_record.concept.name if ir_func_record and ir_func_record.concept else ""

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
        # Step 1: Strip wrappers like %() from each reference before cross-product.
        def strip_wrapper(element: Any) -> Any:
            """Strips the '%...(...)' wrapper if it exists."""
            if isinstance(element, str) and element.startswith("%"):
                # logging.debug(f"Stripping wrapper Element: {element}")
                open_paren_index = element.find("(")
                # To handle nested parentheses in the wrapped content, find the last closing parenthesis.
                close_paren_index = element.rfind(")")

                # Check for a valid wrapper structure, e.g., %code(...)
                if open_paren_index > 0 and close_paren_index == len(element) - 1:
                    return element[open_paren_index + 1 : close_paren_index]
            return element


        # logging.debug(f"Ordered refs: {[ref.tensor for ref in ordered_refs]}")

        stripped_refs = [element_action(strip_wrapper, [ref]) for ref in ordered_refs]

        logging.debug(f"Stripped refs: {[ref.tensor for ref in stripped_refs]}")

        # Step 2: Cross product to get lists of values.
        crossed_ref = cross_product(stripped_refs)

        logging.debug(f"Crossed ref: {crossed_ref.tensor}")

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