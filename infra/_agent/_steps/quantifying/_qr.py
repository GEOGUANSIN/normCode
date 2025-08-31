from types import SimpleNamespace
from typing import Optional
import logging
from infra._states._quantifying_states import States
from infra._core._reference import Reference
from infra._syntax._quantifier import Quantifier
from infra._states._common_states import ReferenceRecordLite

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        logger.warning(
            "[QR] states.syntax is not a dict or SimpleNamespace; QR step requires parsed syntax data. Skipping."
        )
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
        logger.warning("[QR] Missing LoopBaseConcept or ConceptToInfer in syntax data. Skipping.")
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
        logger.warning("[QR] No to-loop elements found in states.values for step 'GR'. Skipping.")
        return states

    # 3) Prepare workspace
    if not hasattr(states, "workspace") or getattr(states, "workspace") is None:
        setattr(states, "workspace", {})
    workspace = getattr(states, "workspace")
    logger.debug(f"[QR Step 3] Workspace: {workspace}")

    # 4) Current loop base element from context (if any)
    current_loop_base_context_item = None
    context_block = getattr(states, "context", []) or []
    for ctx in context_block:
        concept_info = getattr(ctx, "concept", None)
        concept_name = getattr(concept_info, "name", None)
        if concept_name == current_loop_base_concept_name:
            current_loop_base_context_item = ctx
            logger.debug(
                f"[QR Step 4] Found current loop base element in context: {current_loop_base_context_item}"
            )
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

    logger.debug(
        f"[QR Step 5] From function (inner step result): current_concept_element_opt = {current_concept_element_opt.tensor if current_concept_element_opt else 'None'}"
        f"current_loop_base_element_opt = {current_loop_base_element_opt.tensor if current_loop_base_element_opt else 'None'}"
    )
    # 6) Initialize quantifier and retrieve next element
    quantifier = Quantifier(workspace=workspace, loop_base_concept_name=loop_base_concept_name)
    next_current_loop_base_element_opt, _ = quantifier.retireve_next_base_element(
        to_loop_element_reference=to_loop_elements,
        current_loop_base_element=current_loop_base_element_opt,
    )

    logger.debug(
        f"[QR Step 6] Retrieved next element to loop: next_current_loop_base_element_opt = {next_current_loop_base_element_opt.tensor if next_current_loop_base_element_opt else 'None'}"
    )

    # 7) Decide if current loop baseelement is new
    is_new = False
    if current_loop_base_element_opt is not None and isinstance(current_loop_base_element_opt, Reference):
        is_new_check_result = quantifier._check_new_base_element_by_looped_base_element(
            current_looped_element_reference=current_loop_base_element_opt, 
        )
        logger.debug(
            f"[QR Step 7] Checking if '{current_loop_base_element_opt.tensor if current_loop_base_element_opt else 'None'}' is a new base element. Result: {is_new_check_result}"
        )

        if is_new_check_result:
            is_new = True
            current_loop_base_element = current_loop_base_element_opt
            logger.debug(
                f"[QR Step 7] Element IS new. Assigning inner step result to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}"
            )
        else:
            current_loop_base_element = next_current_loop_base_element_opt
            logger.debug(
                f"[QR Step 7] Element is NOT new. Assigning next element to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}"
            )
    else:
        current_loop_base_element = next_current_loop_base_element_opt
        logger.debug(
            f"[QR Step 7] No inner step result. Assigning next element to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}"
        )

    # Store is_quantifier_progress as an attribute of states
    setattr(states, "is_quantifier_progress", is_new)
    logger.debug(f"[QR Step 7] Stored is_quantifier_progress attribute: {is_new}")

    # 8) Ensure references
    next_current_loop_base_element = _ensure_reference(next_current_loop_base_element_opt)
    current_concept_element = _ensure_reference(current_concept_element_opt)
    current_loop_base_element = _ensure_reference(current_loop_base_element)

    # 9) On new element, store base and in-loop concept, but only if they have valid references.
    if is_new:
        if not quantifier._is_reference_empty(current_loop_base_element):
            # First, create the entry for the new base element and get its loop index.
            logger.debug(f"[QR Step 9] Storing NEW base element: {current_loop_base_element.tensor}")
            loop_index = quantifier.store_new_base_element(current_loop_base_element)

            # Now, safely store the inferred concept using the obtained index.
            if not quantifier._is_reference_empty(current_concept_element):
                logger.debug(
                    f"[QR Step 9] Storing in-loop element '{concept_to_infer_name}' with value {current_concept_element.tensor} for base {current_loop_base_element.tensor} at index {loop_index}"
                )
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
            if not isinstance(ctx_name, str):
                continue

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
            new_qr_context_records.append(
                ReferenceRecordLite(step_name="QR", concept=ctx.concept, reference=new_ref_for_qr)
            )

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
    logger.debug("QR completed.")
    return states 