from __future__ import annotations
import os
from typing import Any, Dict, List, TYPE_CHECKING
import logging

from infra._states._judgement_states import States
from infra._core import Reference, cross_product, element_action
from infra._syntax._assigner import Assigner, UnpackedList

if TYPE_CHECKING:
    from infra._agent._body import Body

logger = logging.getLogger(__name__)

# --- Top-Level Helper Functions ---

def _apply_perception_pipeline(element: Any, selector: Dict[str, Any], body: "Body") -> Any:
    """
    Applies perception logic (stripping, wrapping, branching) to a selected element.
    Delegates the actual transformation to the PerceptionRouter.
    """
    # Handle UnpackedList from derelation (apply pipeline to each item)
    if isinstance(element, UnpackedList):
        return UnpackedList([
            body.perception_router.transform(item, selector, body) 
            for item in element
        ])
    
    return body.perception_router.transform(element, selector, body)


def _is_branch_output_dict(d: Dict, body: "Body") -> bool:
    """
    Checks if a dictionary looks like a branch output (values are resolved content)
    rather than a wrapper container (values are wrapped strings).
    """
    if not d:
        return False
    for value in d.values():
        if isinstance(value, str) and body.perception_router.decode_sign(value): # Is it a sign?
            return False  # Contains wrapper/sign, not a branch output
    return True


def _process_and_format_element(element: Any, body: "Body") -> Any:
    """
    The main processing function for each element in a Reference.
    """
    # If this is a dictionary from branch (contains non-wrapper values), preserve it
    if isinstance(element, dict) and _is_branch_output_dict(element, body):
        return element
    
    # If this is an UnpackedList of branch dictionaries, preserve each one
    if isinstance(element, UnpackedList):
        if all(isinstance(item, dict) and _is_branch_output_dict(item, body) for item in element):
            return element
    
    # If this is a regular list of branch dictionaries, preserve each one
    if isinstance(element, list) and all(isinstance(item, dict) and _is_branch_output_dict(item, body) for item in element):
        return element

    flat_list: List[Any] = []
    def flatten(el: Any):
        if isinstance(el, UnpackedList):
             for item in el: flatten(item)
        elif isinstance(el, list):
            for item in el: flatten(item)
        elif isinstance(el, dict):
            # Only flatten dicts that are wrapper containers, not branch outputs
            if _is_branch_output_dict(el, body):
                flat_list.append(el)  # Preserve branch output dicts
            else:
                for value in el.values(): flatten(value)
        else:
            flat_list.append(el)
    
    flatten(element)

    resolved_list = []
    for item in flat_list:
        if isinstance(item, dict):
            # Already a branch dict, keep it
            resolved_list.append(item)
        else:
            # Delegate PERCEPTION to the Body
            resolved_list.append(body.perception_router.perceive(item, body))

    # If any item was resolved into a special instruction, return the list as-is
    # Special instructions often look like {%{key}: value}
    if any(isinstance(s, str) and s.startswith('{%{') for s in resolved_list):
        return resolved_list

    # Otherwise, format into a human-readable string (unless we have dicts)
    if not resolved_list:
        return ""
    
    # If we have dicts (branch outputs), return as-is
    if any(isinstance(item, dict) for item in resolved_list):
        if len(resolved_list) == 1:
            return resolved_list[0]
        return resolved_list
    
    # If we have multiple items, return the list so _format_inputs_as_dict can explode it
    if len(resolved_list) > 1:
        return resolved_list
        
    if len(resolved_list) == 1:
        return str(resolved_list[0])
        
    return str(resolved_list)

def _format_inputs_as_dict(values_list: List[Any], body: "Body") -> Dict[str, Any]:
    """
    Converts a list of processed values into a dictionary.
    """
    output_dict = {}
    inputs = []
    
    # Use keys defined in PerceptionRouter
    special_keys = body.perception_router.SPECIAL_KEYS

    flat_values = []
    for val in values_list:
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

def _get_ordered_input_references(states: States, body: "Body") -> List[Reference]:
    """
    Orders and selects input values from the initial state.
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
                    # 1. Phase 1: Pure Derelation (Structure Selection)
                    derelation_fn = Assigner().derelation(selector)
                    selected_ref = element_action(derelation_fn, [v_record.reference.copy()])
                    
                    # 2. Phase 2: Perception Pipeline (Interpret, Branch, Wrap)
                    # We apply this immediately to resolve wrappers/branches
                    perception_fn = lambda e: _apply_perception_pipeline(e, selector, body)
                    perceived_ref = element_action(perception_fn, [selected_ref])
                    
                    ordered_refs.append(perceived_ref)
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
    Uses the Body's Perception faculty to transmute Signs into Objects.
    """
    logging.debug("--- Starting MVP ---")

    body = states.body

    # 1. Order and select input values from the initial state
    ordered_refs = _get_ordered_input_references(states, body)

    if not ordered_refs:
        states.set_current_step("MVP")
        logging.debug("MVP completed: No ordered references to process.")
        return states

    # 2. Perceive each reference
    processed_refs = [element_action(lambda e: _process_and_format_element(e, body), [ref]) for ref in ordered_refs]

    # 3. Create all combinations of the processed inputs
    crossed_ref = cross_product(processed_refs)

    # 4. Format each combination into a structured dictionary
    dict_ref = element_action(lambda x: _format_inputs_as_dict(x, body), [crossed_ref])
    
    states.set_reference("values", "MVP", dict_ref)

    states.set_current_step("MVP")
    logging.debug(f"MVP completed. Final values set: {states.get_reference('values', 'MVP')}")
    return states
