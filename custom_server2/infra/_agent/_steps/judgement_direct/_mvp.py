import os
from typing import Any, Dict, List
import logging

from infra._states._judgement_direct_states import States
from infra._core import Reference, cross_product, element_action
try:
    from infra._constants import PROJECT_ROOT
except Exception:
    import sys, pathlib
    here = pathlib.Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(here))
    from infra._constants import PROJECT_ROOT

PROMPTS_DIR = os.path.join(PROJECT_ROOT, 'infra', '_agent', '_models', 'prompts')


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
