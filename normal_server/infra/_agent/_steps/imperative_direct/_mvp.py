from __future__ import annotations
import os
from typing import Any, Dict, List, TYPE_CHECKING
import logging
import re

from infra._states._imperative_states import States
from infra._core import Reference, cross_product, element_action
try:
    from infra._constants import PROJECT_ROOT
except Exception:
    import sys, pathlib
    here = pathlib.Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(here))
    from infra._constants import PROJECT_ROOT

if TYPE_CHECKING:
    from infra._agent._models import FileSystemTool

# --- Constants for directory paths ---
PROMPTS_DIR = os.path.join(PROJECT_ROOT, 'infra', '_agent', '_models', 'prompts')
SCRIPTS_DIR = os.path.join(PROJECT_ROOT,'infra', '_agent', '_models', 'scripts')
logger = logging.getLogger(__name__)


# --- Top-Level Helper Functions ---

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

    def nested_selector_action(element):
        return selector_action(element)

    return element_action(nested_selector_action, [ref])

def _read_file_content(location: str) -> str:
    """
    Handles reading a file from a given location.
    Location can be absolute or relative to the infra/_agent/_models/prompts/ directory.
    """
    if os.path.isabs(location):
        file_path = location
    else:
        # For relative paths, we'll check both PROMPTS_DIR and a potential SCRIPTS_DIR or other common places.
        # For now, let's assume prompts is the primary location for such content files.
        file_path = os.path.join(PROMPTS_DIR, location)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        error_msg = f"ERROR: Content file not found at location: {file_path}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"ERROR: Failed to read content file at {file_path}: {e}"
        logger.error(error_msg)
        return error_msg

def _resolve_wrapper_string(item: str, file_system_tool: "FileSystemTool" | None) -> Any:
    """
    Processes a single string that might contain a special wrapper like '%{...}id(...)'
    and returns the resolved content.
    """
    if not isinstance(item, str) or not item.startswith("%{"):
        return item

    pattern = re.compile(r"^%\{(.+?)\}(.*?)\((.+)\)$")
    match = pattern.match(item)

    if not match:
        return item # Not a valid wrapper format

    wrapper_type, unique_id, content = match.groups()
    logger.debug(f"Parsed wrapper: type='{wrapper_type}', id='{unique_id}', content='{content}'")

    # --- Handle wrappers that require the FileSystemTool ---
    if wrapper_type == "memorized_parameter":
        if not file_system_tool:
            error_msg = f"ERROR: FileSystemTool is required to handle '{wrapper_type}' but was not provided."
            return error_msg
        result = file_system_tool.read_memorized_value(content)
        return result.get("content") if result.get("status") == "success" else result.get("message")

    # --- Handle direct prompt reading ---
    elif wrapper_type == "prompt":
        prompt_content = _read_file_content(content)
        return f"{{%{{prompt_template}}: {prompt_content}}}"

    # --- Handle file content reading and treat as a normal input ---
    elif wrapper_type == "file_location":
        return _read_file_content(content)

    # --- Handle wrappers that do not resolve but are reformatted for later steps ---
    elif wrapper_type in ["script_location", "generated_script_path"]:
        return f"{{%{{script_location}}: {content}}}"
    
    elif wrapper_type == "prompt_location":
        return f"{{%{{prompt_location}}: {content}}}"
        
    # --- Fallback for other wrappers: return the content inside the parentheses ---
    else:
        return content

def _process_and_format_element(element: Any, file_system_tool: "FileSystemTool" | None) -> Any:
    """
    The main processing function for each element in a Reference. It flattens
    nested structures, resolves special wrappers, and formats the result.
    """
    flat_list: List[Any] = []
    def flatten(el: Any):
        if isinstance(el, list):
            for item in el: flatten(item)
        elif isinstance(el, dict):
            for value in el.values(): flatten(value)
        else:
            flat_list.append(el)
    
    flatten(element)

    resolved_list = [_resolve_wrapper_string(item, file_system_tool) for item in flat_list]

    # If any item was resolved into a special instruction, return the list as-is
    if any(isinstance(s, str) and s.startswith('{%{') for s in resolved_list):
        return resolved_list

    # Otherwise, format into a human-readable string
    if not resolved_list:
        return ""
    if len(resolved_list) == 1:
        return str(resolved_list[0])
    if len(resolved_list) == 2:
        return f"{resolved_list[0]}, and {resolved_list[1]}"
    return ", ".join(map(str, resolved_list[:-1])) + f", and {resolved_list[-1]}"

def _format_inputs_as_dict(values_list: List[Any]) -> Dict[str, Any]:
    """
    Converts a list of processed values into a dictionary, identifying special
    instructional values and assigning the rest to generic 'input_n' keys.
    """
    output_dict = {}
    inputs = []
    
    special_keys = {
        "prompt_template": "{%{prompt_template}: ",
        "prompt_location": "{%{prompt_location}: ",
        "script_location": "{%{script_location}: ",
    }

    flat_values = []
    for val in values_list:
        if isinstance(val, list):
            flat_values.extend(val)
        else:
            flat_values.append(val)

    for val in flat_values:
        is_special = False
        if isinstance(val, str):
            for key, marker in special_keys.items():
                if val.startswith(marker) and val.endswith("}"):
                    output_dict[key] = val[len(marker):-1]
                    is_special = True
                    break
        if not is_special:
            inputs.append(val)

    # Add the regular inputs with generic keys
    if len(inputs) == 1:
        output_dict["input"] = inputs[0]
    else:
        for i, input_val in enumerate(inputs):
            output_dict[f"input_{i+1}"] = input_val
            
    return output_dict

def _get_ordered_input_references(states: States) -> List[Reference]:
    """
    Orders and selects input values from the initial state based on the
    working configuration (`value_order` and `value_selectors`).
    """
    value_order = states.value_order or {}
    value_selectors = states.value_selectors or {}
    ir_values = [v for v in states.values if v.step_name == "IR" and v.concept and v.reference]
    used_ir_values = [False] * len(ir_values)
    ordered_refs: List[Reference] = []

    sorted_items = sorted(value_order.items(), key=lambda item: item[1])

    for name, _ in sorted_items:
        ref_found = False
        selector = value_selectors.get(name)

        if selector and "source_concept" in selector:
            source_name = selector["source_concept"]
            for i, v_record in enumerate(ir_values):
                if not used_ir_values[i] and v_record.concept.name == source_name:
                    selected_ref = _apply_selector(v_record.reference.copy(), selector)
                    ordered_refs.append(selected_ref)
                    used_ir_values[i] = True
                    ref_found = True
                    break
        else:
            for i, v_record in enumerate(ir_values):
                if not used_ir_values[i] and v_record.concept.name == name:
                    ordered_refs.append(v_record.reference)
                    used_ir_values[i] = True
                    ref_found = True
                    break
        
        if not ref_found:
            logger.warning(f"MVP: Could not find a matching reference for ordered item '{name}'")
    
    return ordered_refs

# --- Main MVP Function ---

def memory_value_perception(states: States) -> States:
    """
    Memory-Value Perception (MVP) step.

    This function acts as a pre-processor for agent inputs. It performs
    the following sequence of operations:
    1.  Orders and selects raw input values based on the configuration.
    2.  Resolves any special "wrapper" directives in the data (e.g., loading
        prompts from files, fetching values from memory).
    3.  Calculates the cross-product of all inputs to prepare for batch
        processing.
    4.  Formats the final combinations of inputs into dictionaries ready for
        the next step (e.g., an LLM call or tool execution).
    """
    logging.debug("--- Starting MVP ---")

    file_system_tool = getattr(states.body, "file_system", None)

    # 1. Order and select input values from the initial state
    ordered_refs = _get_ordered_input_references(states)

    if not ordered_refs:
        states.set_current_step("MVP")
        logging.debug("MVP completed: No ordered references to process.")
        return states

    # 2. Resolve special wrappers in each reference
    processed_refs = [element_action(lambda e: _process_and_format_element(e, file_system_tool), [ref]) for ref in ordered_refs]

    # 3. Create all combinations of the processed inputs
    crossed_ref = cross_product(processed_refs)

    # 4. Format each combination into a structured dictionary
    dict_ref = element_action(_format_inputs_as_dict, [crossed_ref])
    
    states.set_reference("values", "MVP", dict_ref)

    states.set_current_step("MVP")
    logging.debug(f"MVP completed. Final values set: {states.get_reference('values', 'MVP')}")
    return states 