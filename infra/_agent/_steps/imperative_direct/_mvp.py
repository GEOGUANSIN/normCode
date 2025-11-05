import os
from typing import Any, Dict, List
import logging

from infra._states._imperative_states import States
from infra._core import Reference, cross_product, element_action
try:
    from infra._constants import PROJECT_ROOT
except Exception:
    import sys, pathlib
    here = pathlib.Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(here))
    from infra._constants import PROJECT_ROOT

PROMPTS_DIR = os.path.join(PROJECT_ROOT, 'infra', '_agent', '_models', 'prompts')


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
                content = element[open_paren_index + 1: close_paren_index]
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
    logging.debug("--- Starting MVP ---")

    ir_func_record = next((f for f in states.function if f.step_name == "IR"), None)
    func_name = ir_func_record.concept.name if ir_func_record and ir_func_record.concept else ""

    value_order = states.value_order
    value_selectors = states.value_selectors or {}
    logging.debug(f"MVP: value_selectors received: {value_selectors}")

    # Get all value records from the IR step, preserving duplicates.
    ir_values = [v for v in states.values if v.step_name == "IR" and v.concept and v.reference]
    logging.debug(f"MVP: Initial ir_values count: {len(ir_values)}")
    for i, v in enumerate(ir_values):
        logging.debug(f"MVP: ir_values[{i}]: {v.concept.name if v.concept else 'No Concept'}")

    used_ir_values = [False] * len(ir_values)  # Tracker for used records

    ordered_refs: List[Reference] = []
    ordered_names: List[str] = []

    if value_order:
        sorted_items = sorted(value_order.items(), key=lambda item: item[1])
        logging.debug(f"MVP: Processing value_order items: {[item[0] for item in sorted_items]}")

        for name, order_index in sorted_items:  # name is an alias or concept name
            logging.debug(f"MVP: Processing order item '{name}' (index {order_index})")
            ref_found = False

            # Check if the name is an alias defined in the selectors
            selector = value_selectors.get(name)
            if selector and "source_concept" in selector:
                source_name = selector["source_concept"]
                logging.debug(f"MVP: Alias '{name}' found. Needs source_concept: '{source_name}'")
                # Find the first unused record that matches the source concept
                for i, v_record in enumerate(ir_values):
                    logging.debug(f"MVP: Checking ir_values[{i}] ('{v_record.concept.name}')... Used: {used_ir_values[i]}. Match: {v_record.concept.name == source_name}")
                    if not used_ir_values[i] and v_record.concept.name == source_name:
                        logging.debug(f"Applying selector for alias '{name}' using source '{source_name}' (instance {i})")
                        source_ref = v_record.reference
                        # Create a copy to avoid unintended side-effects if a ref is used multiple times
                        selected_ref = _apply_selector(source_ref.copy(), selector)
                        ordered_refs.append(selected_ref)
                        ordered_names.append(name)
                        used_ir_values[i] = True  # Mark this record as used
                        ref_found = True
                        break

            # If not an alias, treat it as a direct concept name
            if not ref_found:
                logging.debug(f"MVP: Alias '{name}' not found in selectors or selector is malformed. Treating as direct concept name.")
                # Find the first unused record that matches the name directly
                for i, v_record in enumerate(ir_values):
                    logging.debug(f"MVP: Checking ir_values[{i}] ('{v_record.concept.name}')... Used: {used_ir_values[i]}. Match: {v_record.concept.name == name}")
                    if not used_ir_values[i] and v_record.concept.name == name:
                        logging.debug(f"Using direct value for '{name}' (instance {i})")
                        ordered_refs.append(v_record.reference)
                        ordered_names.append(name)
                        used_ir_values[i] = True
                        ref_found = True
                        break

            if not ref_found:
                logging.warning(f"MVP: Could not find a matching reference for ordered item '{name}'")

    else:
        # Fallback if no order is specified, though this path is less common with complex inputs
        for v_record in ir_values:
            ordered_refs.append(v_record.reference)
            ordered_names.append(v_record.concept.name)

    if ordered_refs:
        # Step 1: Strip wrappers like %() from each reference before cross-product.
        def prompt_retrieval_wrapper(location: str) -> str:
            """
            Handles the '%{prompt}(location)' wrapper by reading the content from the location.
            Location can be absolute or relative to the infra/_agent/_models/prompts/ directory.
            """
            logger = logging.getLogger(__name__)
            if os.path.isabs(location):
                file_path = location
            else:
                file_path = os.path.join(PROMPTS_DIR, location)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                error_msg = f"ERROR: Prompt file not found at location: {file_path}"
                logger.error(error_msg)
                return error_msg
            except Exception as e:
                error_msg = f"ERROR: Failed to read prompt file at {file_path}: {e}"
                logger.error(error_msg)
                return error_msg

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
                        wrapper_type = item[1:open_paren_index]
                        content = item[open_paren_index + 1 : close_paren_index]
                        
                        if wrapper_type == "{prompt}":
                            prompt_content = prompt_retrieval_wrapper(content)
                            # Create the special string format to mark this as the prompt
                            special_prompt_string = f"{{%{{prompt}}: {prompt_content}}}"
                            stripped_list.append(special_prompt_string)
                        else:
                            stripped_list.append(content)
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
            """
            Creates a dict, identifying the prompt via a special wrapper '{%{prompt}: ...}'
            and assigning other values to keys like 'input_1', 'input_2', etc.
            """
            output_dict = {}
            inputs = []
            
            for val in values_list:
                is_prompt = False
                # Check for our special prompt format
                if isinstance(val, str) and val.startswith("{%{prompt}:") and val.endswith("}"):
                    start_marker = "{%{prompt}: "
                    if val.startswith(start_marker):
                        content = val[len(start_marker):-1]
                        output_dict["prompt_template"] = content
                        is_prompt = True

                if not is_prompt:
                    inputs.append(val)

            # Add the regular inputs with generic keys
            for i, input_val in enumerate(inputs):
                output_dict[f"input_{i+1}"] = input_val
                
            return output_dict

        dict_ref = element_action(list_to_dict, [crossed_ref])
        states.set_reference("values", "MVP", dict_ref)

    states.set_current_step("MVP")
    logging.debug(f"MVP completed. Values state after cross-product and dict conversion: {states.values}")
    return states 