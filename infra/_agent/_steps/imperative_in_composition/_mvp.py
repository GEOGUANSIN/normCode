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
    from infra._agent._models._prompt import PromptTool

# --- Constants for directory paths ---
PROMPTS_DIR = os.path.join(PROJECT_ROOT, 'infra', '_agent', '_models', 'prompts')
SCRIPTS_DIR = os.path.join(PROJECT_ROOT,'infra', '_agent', '_models', 'scripts')
logger = logging.getLogger(__name__)


class UnpackedList(list):
    """Wrapper to signal that a list should be exploded into multiple inputs."""
    pass


# --- Top-Level Helper Functions ---

def _apply_selector(ref: Reference, selector: Dict[str, Any]) -> Reference:
    """Applies a selector to a reference to extract a specific value."""
    index = selector.get("index")
    key = selector.get("key")
    unpack = selector.get("unpack", False)
    unpack_before = selector.get("unpack_before_selection", False)
    strip_wrapper = selector.get("strip_wrapper", False)
    new_wrapper = selector.get("new_wrapper")

    def selector_action(element):
        import ast

        def strip(val):
            if isinstance(val, str) and val.startswith("%"):
                open_paren_index = val.find("(")
                close_paren_index = val.rfind(")")
                if open_paren_index > 0 and close_paren_index == len(val) - 1:
                    content = val[open_paren_index + 1: close_paren_index]
                    try:
                        return ast.literal_eval(content)
                    except (ValueError, SyntaxError):
                        return content
            return val

        processed_element = strip(element)
        
        # Determine starting point. 
        # If we need to drill down (key/index/unpack_before), we MUST work on the stripped/processed element.
        # If strip_wrapper is requested, we also start with processed (though it might be a container).
        use_processed = (strip_wrapper or new_wrapper is not None or unpack_before or key is not None or index is not None)
        target = processed_element if use_processed else element

        def process_final_item(val):
            # If explicitly stripping or re-wrapping, ensure we strip any wrapper on the final item
            if strip_wrapper or new_wrapper:
                val = strip(val)
            
            if new_wrapper and val is not None:
                return f"%{{{new_wrapper}}}id({val})"
            return val

        # Branch 1: Unpack Before Selection
        if unpack_before and isinstance(target, list):
            results = []
            for item in target:
                selected_item = item
                if key is not None and isinstance(selected_item, dict):
                    selected_item = selected_item.get(key)
                results.append(process_final_item(selected_item))
            return UnpackedList(results)

        # Branch 2: Standard Selection (Unpack After)
        selected = target
        if index is not None and isinstance(selected, list) and len(selected) > index:
            selected = selected[index]

        if key is not None and isinstance(selected, dict):
            selected = selected.get(key)

        if unpack and isinstance(selected, list):
            return UnpackedList([process_final_item(item) for item in selected])

        return process_final_item(selected)

    def nested_selector_action(element):
        return selector_action(element)

    return element_action(nested_selector_action, [ref])

def _read_file_content(location: str, file_system_tool: "FileSystemTool" | None) -> str:
    """
    Handles reading a file from a given location using the file system tool.
    The tool correctly resolves paths relative to its configured base_dir.
    """
    if not file_system_tool:
        return f"ERROR: FileSystemTool is required to read '{location}' but was not provided."

    result = file_system_tool.read(location)
    if result.get("status") == "success":
        return result.get("content", "")
    else:
        # The file_system_tool.read method should now return a helpful message.
        error_msg = result.get("message", f"ERROR: An unknown error occurred while reading {location}")
        logger.error(error_msg)
        return error_msg

def _resolve_wrapper_string(item: str, file_system_tool: "FileSystemTool" | None, prompt_tool: "PromptTool" | None) -> Any:
    """
    Processes a single string that might contain a special wrapper like '%{...}id(...)'
    and returns the resolved content.
    """
    if not isinstance(item, str) or not item.startswith("%"):
        return item

    # --- Handle simple wrappers like %id(value) first ---
    simple_pattern = re.compile(r"^%[a-zA-Z0-9]+\((.*)\)$")
    simple_match = simple_pattern.match(item)
    if simple_match:
        return simple_match.group(1)

    # --- Handle complex wrappers like %{type}id(value) ---
    if not item.startswith("%{"):
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
        prompt_content = _read_file_content(content, file_system_tool)
        return f"{{%{{prompt_template}}: {prompt_content}}}"

    # --- Handle file content reading and treat as a normal input ---
    elif wrapper_type == "file_location":
        return _read_file_content(content, file_system_tool)

    # --- Handle wrappers that do not resolve but are reformatted for later steps ---
    elif wrapper_type in ["script_location", "generated_script_path"]:
        return f"{{%{{script_location}}: {content}}}"
    
    elif wrapper_type == "prompt_location":
        if not prompt_tool:
            return f"ERROR: PromptTool is required to handle '{wrapper_type}'"
        try:
            prompt_template = prompt_tool.read(content)
            return f"{{%{{prompt_template}}: {prompt_template.template}}}"
        except FileNotFoundError as e:
            logger.error(f"Error reading prompt for '{content}': {e}")
            return f"ERROR: Prompt not found: {content}"

    elif wrapper_type == "save_path":
        return f"{{%{{save_path}}: {content}}}"

    elif wrapper_type == "save_dir":
        return f"{{%{{save_dir}}: {content}}}"
        
    # --- Fallback for other wrappers: return the content inside the parentheses ---
    else:
        return content

def _process_and_format_element(element: Any, file_system_tool: "FileSystemTool" | None, prompt_tool: "PromptTool" | None) -> Any:
    """
    The main processing function for each element in a Reference. It flattens
    nested structures, resolves special wrappers, and formats the result.
    """
    flat_list: List[Any] = []
    def flatten(el: Any):
        if isinstance(el, UnpackedList):
             # Preserve UnpackedList structure so we can distinguish it later,
             # but we still need to process its children.
             # Actually, to process children, we might need to flatten it temporarily
             # or handle it specifically.
             # Let's treat UnpackedList as a list that we MUST flatten into the main flow
             # but we need to resolve wrappers inside it first.
             for item in el: flatten(item)
        elif isinstance(el, list):
            for item in el: flatten(item)
        elif isinstance(el, dict):
            for value in el.values(): flatten(value)
        else:
            flat_list.append(el)
    
    flatten(element)

    resolved_list = [_resolve_wrapper_string(item, file_system_tool, prompt_tool) for item in flat_list]

    # If any item was resolved into a special instruction, return the list as-is
    if any(isinstance(s, str) and s.startswith('{%{') for s in resolved_list):
        return resolved_list

    # Otherwise, format into a human-readable string
    if not resolved_list:
        return ""
    
    # If we have multiple items, return the list so _format_inputs_as_dict can explode it
    if len(resolved_list) > 1:
        return resolved_list
        
    if len(resolved_list) == 1:
        return str(resolved_list[0])
        
    return str(resolved_list)

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
        "save_path": "{%{save_path}: ",
        "save_dir": "{%{save_dir}: ",
    }

    flat_values = []
    for val in values_list:
        # Always explode lists, whether they are UnpackedList or regular list,
        # because _process_and_format_element flattens everything anyway.
        if isinstance(val, list) or isinstance(val, UnpackedList):
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
                if v_record.concept.name == source_name:
                    selected_ref = _apply_selector(v_record.reference.copy(), selector)
                    ordered_refs.append(selected_ref)
                    # Do NOT mark as used here, so other selectors can use it too
                    # used_ir_values[i] = True 
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
    prompt_tool = getattr(states.body, "prompt_tool", None)

    # 1. Order and select input values from the initial state
    ordered_refs = _get_ordered_input_references(states)

    if not ordered_refs:
        states.set_current_step("MVP")
        logging.debug("MVP completed: No ordered references to process.")
        return states

    # 2. Resolve special wrappers in each reference
    processed_refs = [element_action(lambda e: _process_and_format_element(e, file_system_tool, prompt_tool), [ref]) for ref in ordered_refs]

    # 3. Create all combinations of the processed inputs
    crossed_ref = cross_product(processed_refs)

    # 4. Format each combination into a structured dictionary
    dict_ref = element_action(_format_inputs_as_dict, [crossed_ref])
    
    states.set_reference("values", "MVP", dict_ref)

    states.set_current_step("MVP")
    logging.debug(f"MVP completed. Final values set: {states.get_reference('values', 'MVP')}")
    return states