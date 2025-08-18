import os
import sys
import logging
from typing import Any, Dict, List, Optional, Callable, Tuple
from types import SimpleNamespace
from dataclasses import dataclass, field
from string import Template
from copy import copy

# Ensure this directory is importable regardless of where the script is run from
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from infra._core import Inference, register_inference_sequence, setup_logging
from infra._core import Concept
from infra._core import Reference, cross_product, cross_action, element_action
from infra._common.grouper import Grouper
from infra._states.quantifying_states import States
from infra._common.quantifier import Quantifier
from infra._agent._steps.quantifying import (
    iwi,
    ir,
    gr,
    qr,
    or_step,
    owi,
)


# --- State Models (adapted from grouping_sequence_runner.py) ---


# --- Sequence Step Implementations ---

def input_working_interpretation(
    inference: Inference, 
    states: States, 
    working_interpretation: Optional[Dict[str, Any]] = None
) -> States:
    """Initialize states with syntax info and placeholder records."""
    if working_interpretation:
        states.syntax = SimpleNamespace(**working_interpretation.get("syntax", {}))

    # Clear previous state to prevent accumulation in loops
    states.function = []
    states.values = []
    states.context = []
    states.inference = []

    # Seed lists with empty records for each step
    for step in ["GR", "QR", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logging.debug(f"IWI completed. Syntax: {states.syntax}")
    return states

def input_references(inference: Inference, states: States) -> States:
    """Populate references and concept info into the state from the inference instance."""
    # This logic is identical to the grouping runner
    if inference.function_concept:
        states.function.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(id=inference.function_concept.id, name=inference.function_concept.name, type=inference.function_concept.type, context=inference.function_concept.context, axis_name=inference.function_concept.axis_name),
                reference=inference.function_concept.reference.copy() if inference.function_concept.reference else None
            )
        )
    
    for vc in inference.value_concepts or []:
        # Store GR concepts under 'GR' to be used by QR later.
        states.values.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(id=vc.id, name=vc.name, type=vc.type, context=vc.context, axis_name=vc.axis_name),
                reference=vc.reference.copy() if vc.reference else None
            )
        )
    
    for cc in inference.context_concepts or []:
        states.context.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(id=cc.id, name=cc.name, type=cc.type, context=cc.context, axis_name=cc.axis_name),
                reference=cc.reference.copy() if cc.reference else None
            )
        )
    
    states.set_current_step("IR")
    logging.debug(f"IR completed. Loaded {len(states.values)} value and {len(states.context)} context concepts.")
    return states

def grouping_references(states: States) -> States:
    """Perform the core grouping logic for quantification."""
    # 1. Get value references to be grouped.
    value_refs = [r.reference.copy() for r in states.values if r.reference and r.step_name == 'IR']
    if not value_refs:
        logging.warning("[GR] No value references found for grouping.")
        states.set_current_step("GR")
        return states

    # 2. Find the axis of the concept we are looping over from the value concepts.
    loop_base_concept_name = getattr(states.syntax, 'LoopBaseConcept', None)
    loop_base_axis = None
    if loop_base_concept_name:
        loop_base_axis = next(
            (r.concept.axis_name for r in states.values 
             if r.concept and r.concept.name == loop_base_concept_name), 
            None
        )
    
    if not loop_base_axis and value_refs[0].axes:
        loop_base_axis = value_refs[0].axes[0]
        logging.warning(f"Loop base axis not found for '{loop_base_concept_name}'. Falling back to '{loop_base_axis}'.")

    # 3. Perform grouping. For quantification, this is essentially a flattening operation.
    grouper = Grouper()
    # For quantification, we always use or_across pattern
    # Pass a copy of the axes to prevent destructive modification of the original reference.
    by_axes = [ref.axes.copy() for ref in value_refs]
    to_loop_ref = grouper.or_across(
        references=value_refs, 
        by_axes=by_axes,
    )


    current_loop_base_concept_name = f"{getattr(states.syntax, 'LoopBaseConcept', None)}*" if getattr(states.syntax, 'LoopBaseConcept', None) else None
    # Safely get the axis name from the concept, not the reference.
    current_loop_base_concept_axis = next((r.concept.axis_name for r in states.context if r.concept and r.concept.name == current_loop_base_concept_name), None)


    if current_loop_base_concept_axis:
        if to_loop_ref.axes == ["_none_axis"]:
            new_axes = [current_loop_base_concept_axis]
        else:
            new_axes = to_loop_ref.axes.copy() + [current_loop_base_concept_axis] 
        to_loop_ref.axes = new_axes


    states.values.append(ReferenceRecordLite(step_name="GR", reference=to_loop_ref.copy()))
   
    states.set_current_step("GR")
    logging.debug("GR completed.")
    return states

def quantifying_references(states: States) -> States:
    """
    Quantifying References (QR) step using only the `states` object.
    """
    def _ensure_reference(ref: Optional[Reference]) -> Reference:
        if isinstance(ref, Reference):
            return ref
        return Reference(axes=[], shape=())

    # 1) Read syntax data (parsed quantification)
    syntax_data = getattr(states, "syntax", {})
    if not isinstance(syntax_data, SimpleNamespace) and not isinstance(syntax_data, dict):
        logging.warning("[QR] states.syntax is not a dict or SimpleNamespace; QR step requires parsed syntax data. Skipping.")
        return states
    
    # Handle both SimpleNamespace and dict for syntax_data
    def get_syntax_attr(attr, default=None):
        if isinstance(syntax_data, SimpleNamespace):
            return getattr(syntax_data, attr, default)
        return syntax_data.get(attr, default)

    loop_base_concept_name = get_syntax_attr("LoopBaseConcept")
    concept_to_infer_list = get_syntax_attr("ConceptToInfer", [])
    in_loop_spec = get_syntax_attr("InLoopConcept")

    if not loop_base_concept_name or not concept_to_infer_list:
        logging.warning("[QR] Missing LoopBaseConcept or ConceptToInfer in syntax data. Skipping.")
        return states
    concept_to_infer_name = concept_to_infer_list[0]
    current_loop_base_concept_name = f"{loop_base_concept_name}*"

    # 2) Get to-loop elements reference (from GR step)
    to_loop_elements: Optional[Reference] = None
    values_block = getattr(states, "values", []) or []
    for item in values_block:
        if getattr(item, "step_name", None) == "GR" and getattr(item, "reference", None) is not None:
            to_loop_elements = item.reference
            break
    if to_loop_elements is None:
        logging.warning("[QR] No to-loop elements found in states.values for step 'GR'. Skipping.")
        return states

    # 3) Prepare workspace
    if not hasattr(states, "workspace") or getattr(states, "workspace") is None:
        setattr(states, "workspace", {})
    workspace = getattr(states, "workspace")

    # 4) Current loop base element from context (if any)
    current_loop_base_context_item = None
    context_block = getattr(states, "context", []) or []
    for ctx in context_block:
        concept_info = getattr(ctx, "concept", None)
        concept_name = getattr(concept_info, "name", None)
        if concept_name == current_loop_base_concept_name:
            current_loop_base_context_item = ctx
            logging.debug(f"[QR Step 4] Found current loop base element in context: {current_loop_base_context_item}")
            break
    
    current_loop_base_element_opt = None
    if current_loop_base_context_item is not None:
        current_loop_base_element_opt = getattr(current_loop_base_context_item, "reference", None)

    # 5) Determine current concept element from function block (first available reference)
    current_concept_element_opt = None
    function_block = getattr(states, "function", []) or []
    for fn in function_block:
        ref = getattr(fn, "reference", None)
        if ref is not None:
            current_concept_element_opt = ref
            break

    logging.debug(f"[QR Step 5] From function (inner step result): current_concept_element_opt = {current_concept_element_opt.tensor if current_concept_element_opt else 'None'}")
    # 6) Initialize quantifier and retrieve next element
    quantifier = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    next_current_loop_base_element_opt, _ = quantifier.retireve_next_base_element(
        to_loop_element_reference=to_loop_elements,
        current_loop_base_element=current_concept_element_opt,
    )

    logging.debug(f"[QR Step 6] Retrieved next element to loop: next_current_loop_base_element_opt = {next_current_loop_base_element_opt.tensor if next_current_loop_base_element_opt else 'None'}")

    # 7) Decide if current element is new
    is_new = False
    if current_concept_element_opt is not None and isinstance(current_concept_element_opt, Reference):
        is_new_check_result = quantifier._check_new_base_element_by_looped_base_element(current_concept_element_opt, current_loop_base_concept_name)
        logging.debug(f"[QR Step 7] Checking if '{current_concept_element_opt.tensor if current_concept_element_opt else 'None'}' is a new base element. Result: {is_new_check_result}")

        if is_new_check_result:
            is_new = True
            current_loop_base_element = current_concept_element_opt
            logging.debug(f"[QR Step 7] Element IS new. Assigning inner step result to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}")
        else:
            current_loop_base_element = next_current_loop_base_element_opt
            logging.debug(f"[QR Step 7] Element is NOT new. Assigning next element to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}")
    else:
        current_loop_base_element = next_current_loop_base_element_opt
        logging.debug(f"[QR Step 7] No inner step result. Assigning next element to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}")

    # 8) Ensure references
    next_current_loop_base_element = _ensure_reference(next_current_loop_base_element_opt)
    current_concept_element = _ensure_reference(current_concept_element_opt)
    current_loop_base_element = _ensure_reference(current_loop_base_element)

    # 9) On new element, store base and in-loop concept, but only if they have valid references.
    if is_new:
        if not quantifier._is_reference_empty(current_loop_base_element):
            # First, create the entry for the new base element and get its loop index.
            logging.debug(f"[QR Step 9] Storing NEW base element: {current_loop_base_element.tensor}")
            loop_index = quantifier.store_new_base_element(current_loop_base_element)
            
            # Now, safely store the inferred concept using the obtained index.
            if not quantifier._is_reference_empty(current_concept_element):
                logging.debug(f"[QR Step 9] Storing in-loop element '{concept_to_infer_name}' with value {current_concept_element.tensor} for base {current_loop_base_element.tensor} at index {loop_index}")
                quantifier.store_new_in_loop_element(
                    current_loop_base_element,
                    concept_to_infer_name,
                    current_concept_element,
                )

    # 10) Update context: Create new 'QR' step records for the inner loop's context.
    new_qr_context_records = []
    for ctx in context_block:
        concept_info = getattr(ctx, "concept", None)
        ctx_name = getattr(concept_info, "name", None)
        new_ref_for_qr = None

        # Determine the new reference for the loop base concept
        if ctx_name == current_loop_base_concept_name:
            new_ref_for_qr = next_current_loop_base_element.copy()

        # Determine the new reference for any in-loop concepts to be carried over
        elif in_loop_spec is not None and ctx_name in in_loop_spec:
            if not isinstance(ctx_name, str): continue
            
            # For new elements, store the initial value of the in-loop concept (e.g., initial partial_sum).
            if is_new and not quantifier._is_reference_empty(current_loop_base_element):
                quantifier.store_new_in_loop_element(
                    current_loop_base_element,
                    ctx_name,
                    _ensure_reference(getattr(ctx, "reference", None)),
                )
            carry_index = in_loop_spec[ctx_name]
            new_ref_for_qr = quantifier.retrieve_next_in_loop_element(
                ctx_name,
                current_loop_index=carry_index,
            )
        
        # If an updated reference was created, add it to our list for the new QR context.
        if new_ref_for_qr:
            new_qr_context_records.append(ReferenceRecordLite(
                step_name="QR",
                concept=ctx.concept,
                reference=new_ref_for_qr
            ))

    # Prepend the new QR records to the list so they are found first. The original IR records are preserved.
    states.context = new_qr_context_records + states.context

    # 11) Combine all stored references for the inferred concept
    combined_reference: Optional[Reference] = None
    if is_new:
        combined_reference = quantifier.combine_all_looped_elements_by_concept(
            to_loop_element_reference=to_loop_elements,
            concept_name=concept_to_infer_name,
        )
        if combined_reference is not None:
            # Axis normalization
            loop_base_axis, current_loop_axis = None, None
            for v in values_block:
                ci = getattr(v, "concept", None)
                if ci and getattr(ci, "name", None) == loop_base_concept_name:
                    loop_base_axis = getattr(ci, "axis_name", None)
                    break
            for c in context_block:
                ci = getattr(c, "concept", None)
                if ci and getattr(ci, "name", None) == current_loop_base_concept_name:
                    current_loop_axis = getattr(ci, "axis_name", None)
                    break

            if loop_base_axis is not None and current_loop_axis is not None:
                new_axes = combined_reference.axes.copy()
                new_axes[-1] = concept_to_infer_name
                if current_loop_axis in new_axes:
                    new_axes[new_axes.index(current_loop_axis)] = loop_base_axis
                combined_reference.axes = new_axes

    # 12) Write result into states.inference under QR if the entry exists
    if combined_reference is not None:
        for inf in getattr(states, "inference", []) or []:
            if getattr(inf, "step_name", None) == "QR":
                setattr(inf, "reference", combined_reference)
                break
    
    states.set_current_step("QR")
    logging.debug("QR completed.")
    return states


def output_reference(states: States) -> States:
    """Finalize the output reference and context from the QR step."""
    # The final result is the one produced by the QR step.
    qr_ref = states.get_reference("inference", "QR")
    if qr_ref:
        states.set_reference("inference", "OR", qr_ref)

    # Copy QR context records to be the new OR context records for the next iteration.
    or_context_records = [
        ReferenceRecordLite(
            step_name="OR",
            concept=ctx.concept,
            reference=ctx.reference.copy() if ctx.reference else None
        ) 
        for ctx in states.context if ctx.step_name == 'QR'
    ]
    
    # Keep all non-OR records and add the new OR records.
    non_or_context = [c for c in states.context if c.step_name != 'OR']
    states.context = or_context_records + non_or_context

    states.set_current_step("OR")
    logging.debug("OR completed.")
    return states

def output_working_interpretation(states: States) -> States:
    """Check for loop completion and set status."""
    
    syntax_data = getattr(states, "syntax", {})
    loop_base_concept_name = getattr(syntax_data, "LoopBaseConcept", None)
    
    to_loop_elements = None
    values_block = getattr(states, "values", []) or []
    for item in values_block:
        if (getattr(item, "step_name", None) == "GR" and 
            getattr(item, "reference", None) is not None):
            to_loop_elements = item.reference
            break
            
    is_complete = False
    logging.debug(f"[OWI Step 1] Checking if loop is complete. Loop base concept name: {loop_base_concept_name}, To loop elements: {to_loop_elements}")
    if loop_base_concept_name and to_loop_elements:
        quantifier = Quantifier(workspace=states.workspace, loop_base_concept_name=loop_base_concept_name)
        concept_to_infer_name = (getattr(syntax_data, "ConceptToInfer") or [""])[0]
        if quantifier.check_all_base_elements_looped(to_loop_elements, in_loop_element_name=concept_to_infer_name):
            is_complete = True

    setattr(states.syntax, 'completion_status', is_complete)
    
    states.set_current_step("OWI")
    logging.debug(f"OWI completed. Completion status: {is_complete}")
    return states

# --- Logging ---
def log_states_progress(states: States, step_name: str, step_filter: Optional[str] = None):
    logger = logging.getLogger(__name__)
    logger.info(f"--- States after {step_name} (Filtered by: {step_filter or 'None'}) ---")
    logger.info(f"Current Step: {states.sequence_state.current_step}")
    
    def _log_record_list(label: str, record_list: List[ReferenceRecordLite]):
        logger.info(f"{label}:")
        filtered_records = [item for item in record_list if step_filter is None or item.step_name == step_filter]
        if not filtered_records:
            logger.info("  (Empty or no matching records for filter)")
            return
        for item in filtered_records:
            logger.info(f"  Step Name: {item.step_name}")
            if item.concept:
                logger.info(f"    Concept: Name={item.concept.name}, Axis={item.concept.axis_name}")
            if item.reference and isinstance(item.reference, Reference):
                logger.info(f"    Reference: Axes={item.reference.axes}, Shape={item.reference.shape}")
                # Log tensor but truncate if too long
                tensor_str = str(item.reference.tensor)
                logger.info(f"    Tensor: {tensor_str[:200]}{'...' if len(tensor_str) > 200 else ''}")

    _log_record_list("Function", states.function)
    _log_record_list("Values", states.values)
    _log_record_list("Context", states.context)
    _log_record_list("Inference", states.inference)
    logger.info("-" * 20)


# --- Quantifying Sequence Runner ---

@register_inference_sequence("quantifying_v2")
def quantifying_v2(self: Inference, input_data: Optional[Dict[str, Any]] = None) -> States:
    """New quantifying sequence runner."""
    # Check if a persistent state is being passed in
    states = (input_data or {}).get("initial_states")
    if not isinstance(states, States):
        states = States()

    working_interpretation = (input_data or {}).get("working_interpretation")

    # IWI
    states = iwi.input_working_interpretation(
        self, states, working_interpretation=working_interpretation
    )
    log_states_progress(states, "IWI")
    # IR
    states = ir.input_references(self, states)
    log_states_progress(states, "IR")
    # GR
    states = gr.grouping_references(states)
    log_states_progress(states, "GR", step_filter="GR")
    # QR
    states = qr.quantifying_references(states)
    log_states_progress(states, "QR", step_filter="QR")
    # OR
    states = or_step.output_reference(states)
    log_states_progress(states, "OR", step_filter="OR")
    # OWI
    states = owi.output_working_interpretation(states)
    log_states_progress(states, "OWI")

    return states


# --- Demo Setup: Summing Digits ---

def _build_demo_concepts_for_quant_controller() -> tuple[Concept, List[Concept], Concept, List[Concept]]:
    """Builds concepts for the outer quantification controller."""
    # Value Concept: The list of digits to be looped over.
    ref_digits = Reference(axes=["digit_pos"], shape=(4,))
    for i, v in enumerate([1, 8, 2, 5]):
        ref_digits.set(f"%({v})", digit_pos=i)
    concept_digits = Concept("{digit}", "digit", "digit_pos", ref_digits)

    # Context Concepts for Loop Control
    concept_current_digit = Concept("{digit}*", "digit*", "digit*")
    concept_partial_sum = Concept("{partial_sum}*", "partial_sum*", "partial_sum*")

    # Placeholder for the function concept, which will be the *result* of the inner imperative step
    quantification_concept = Concept("::(add_result)", "add_result", "f", Reference(axes=["f"], shape=(1,)))

    # Concept to Infer: The final accumulated sum.
    concept_to_infer = Concept("{sum}", "sum", "sum")

    return (
        concept_to_infer,
        [concept_digits],
        quantification_concept,
        [concept_current_digit, concept_partial_sum]
    )

def _build_demo_working_interpretation() -> Dict[str, Any]:
    """Provides the syntax needed for the QR step."""
    return {
        "syntax": {
            "marker": None, 
            "LoopBaseConcept": "{digit}",
            "ConceptToInfer": ["{sum}"],
            "InLoopConcept": {
                "{partial_sum}*": 1  # Carry over partial sum from 1 step ago
            },
            "completion_status": False
        }
    }

# --- Utility Functions ---
def _get_workspace_tensor_view(workspace: Dict) -> Dict:
    """Recursively converts a workspace of Reference objects to a dictionary of their tensors."""
    tensor_view = {}
    for key, value in workspace.items():
        if isinstance(value, dict):
            tensor_view[key] = _get_workspace_tensor_view(value)
        elif hasattr(value, 'tensor'): # Check if it's a Reference-like object
            tensor_view[key] = value.tensor
        else:
            tensor_view[key] = value
    return tensor_view

# --- Main Execution ---

def run_quantifying_sequence() -> States:
    """Demonstrates the iterative controller-actor pattern for quantification."""
    setup_logging(logging.DEBUG)

    # --- Mock Inner "Imperative" Sequence ---
    def mock_imperative_add_step(current_digit_concept: Concept, partial_sum_concept: Concept) -> Concept:
        """Simulates an inner sequence that performs addition for one loop step."""
        # Strip wrappers like %() to get raw numbers
        try:
            current_digit = int(str(current_digit_concept.reference.copy().tensor[0]).strip("%()"))
        except (AttributeError, IndexError, ValueError):
            current_digit = 0
        try:
            partial_sum = int(str(partial_sum_concept.reference.copy().tensor[0]).strip("%()"))
        except (AttributeError, IndexError, ValueError, TypeError):
            partial_sum = 1  # Default to 0 if no partial sum yet

        new_sum = current_digit + partial_sum
        logging.info(f"[Inner Worker] Adding {current_digit} + {partial_sum} = {new_sum}")

        # The result is a new concept holding the calculated sum
        ref_new_sum = Reference(axes=["sum"], shape=(1,)); ref_new_sum.set(f"%({new_sum})", sum=0)
        return Concept("{new_sum}", "new_sum", "sum", ref_new_sum)

    # --- Setup for Outer "Quantifying" Controller ---
    concept_to_infer, value_concepts, quantification_concept, context_concepts = _build_demo_concepts_for_quant_controller()
    
    quantification_inference = Inference(
        "quantifying_v2",
        concept_to_infer,
        value_concepts,
        quantification_concept, # Starts with a placeholder
        context_concepts=context_concepts
    )
    
    # --- Main Execution Loop ---
    working_interpretation = _build_demo_working_interpretation()
    iteration = 0
    
    # We need a state object that persists across loop iterations
    states = States()

    while not working_interpretation.get("syntax", {}).get("completion_status", False):
        iteration += 1
        logging.info(f"--- QUANTIFICATION LOOP: ITERATION {iteration} ---")
        if iteration > 5: # Safety break
            logging.warning("Safety break triggered to prevent infinite loop.")
            break

        # 1. Run the controller to get the current state and context for the inner worker
        logging.info("[Controller] Running to get context for inner worker...")
        
        # Pass the whole states object to persist workspace and other attributes
        workspace_tensor = _get_workspace_tensor_view(states.workspace)
        states = quantification_inference.execute(input_data={"working_interpretation": working_interpretation, "initial_states": states, "initial_workspace": workspace_tensor})
        
        # Check if the loop is complete right after the execution runs
        if states.syntax.completion_status == True:
            logging.info("[Controller] Loop is complete. Exiting loop.")
            break

        # Extract the current digit and partial sum from the controller's 'OR' context
        current_digit_ctx = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{digit}*"), Concept("","", "", Reference(axes=[], shape=())))
        partial_sum_ctx = next((c for c in states.context if c.step_name == 'OR' and c.concept and c.concept.name == "{partial_sum}*"), Concept("","", "", Reference(axes=[], shape=())))

        logging.info(f"[Controller] Current digit context for worker: {current_digit_ctx.reference.tensor}")
        logging.info(f"[Controller] Partial sum context for worker: {partial_sum_ctx.reference.tensor}")

        # 2. Run the inner worker (mocked) with the context provided by the controller
        new_sum_concept = mock_imperative_add_step(current_digit_ctx, partial_sum_ctx)

        # 3. Feed the result of the inner worker back to the controller
        # The result becomes the "function_concept" for the controller's next run
        quantification_inference.function_concept = new_sum_concept

        # 4. Renew the context concepts in the states object
        [current_digit, partial_sum] = context_concepts
        current_digit.reference = current_digit_ctx.reference.copy()
        partial_sum.reference = partial_sum_ctx.reference.copy()
        quantification_inference.context_concepts = [current_digit, partial_sum]
        
        # Update the working interpretation with the latest completion status from the state
        if hasattr(states, 'syntax') and hasattr(states.syntax, 'completion_status'):
            working_interpretation["syntax"]["completion_status"] = states.syntax.completion_status
        else:
            working_interpretation["syntax"]["completion_status"] = True # Failsafe

    logging.info("--- QUANTIFICATION COMPLETE ---")
    
    # Final state after loop terminates
    final_states = states
    final_ref = final_states.get_reference("inference", "OR")

    # Final log
    logger = logging.getLogger(__name__)
    if isinstance(final_ref, Reference):
        logger.info("--- Final Output (OR) ---")
        tensor_content = final_ref.get_tensor(ignore_skip=True)
        logger.info(f"Final Tensor: {tensor_content}")
        print("\n--- Final Output (OR) ---")
        # The result is a list of all the intermediate sums
        print(f"Tensor: {tensor_content}")
        # Expected: [['%(1)'], ['%(9)'], ['%(11)'], ['%(16)']]
    
    return final_states

if __name__ == "__main__":
    run_quantifying_sequence() 