from types import SimpleNamespace
from typing import Optional
import logging
from infra._states._looping_states import States
from infra._core._reference import Reference
from infra._syntax._looper import Looper
from infra._states._common_states import ReferenceRecordLite
from infra._loggers.utils import log_workspace_details

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def looping_references(states: States) -> States:
    """
    Looping References (LR) step using only the `states` object.
    """

    def _ensure_reference(ref: Optional[Reference]) -> Reference:
        if isinstance(ref, Reference):
            return ref
        return Reference(axes=[], shape=())

    # 1) Read syntax data (parsed loop specification)
    syntax_data = getattr(states, "syntax", {})
    if not isinstance(syntax_data, SimpleNamespace) and not isinstance(
        syntax_data, dict
    ):
        logger.warning(
            "[LR] states.syntax is not a dict or SimpleNamespace; "
            "LR step requires parsed syntax data. Skipping."
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
    loop_index = get_syntax_attr("loop_index", 0)

    # Resolve in-loop concept names, supporting both old and new syntax formats for backward compatibility.
    resolved_in_loop_concepts = {}
    if in_loop_spec:
        for name, spec in in_loop_spec.items():
            if isinstance(spec, int):
                # Old format compatibility: {"{index}*": 1}
                current_name = name
                base_name = (
                    current_name[:-1]
                    if current_name.endswith("*")
                    else current_name
                )
                resolved_in_loop_concepts[current_name] = {
                    "carry_over": spec,
                    "base_name": base_name,
                }
            elif isinstance(spec, dict):
                # New format: {"{index}": {"current_name": "{index}*", "carry_over": 1}}
                base_name = name
                current_name = spec.get("current_name")
                if not current_name:
                    current_name = f"{base_name}*"
                resolved_in_loop_concepts[current_name] = {
                    "carry_over": spec.get("carry_over", 0),
                    "base_name": base_name,
                }

    if not loop_base_concept_name or not concept_to_infer_list:
        logger.warning(
            "[LR] Missing LoopBaseConcept or ConceptToInfer in syntax data. Skipping."
        )
        return states
    concept_to_infer_name = concept_to_infer_list[0]

    # Determine the name for the current loop item, using explicit syntax first, then falling back to convention.
    current_loop_base_concept_name = get_syntax_attr("CurrentLoopBaseConcept")
    if not current_loop_base_concept_name:
        current_loop_base_concept_name = f"{loop_base_concept_name}*"

    # 2) Get to-loop elements reference (from GR step)
    to_loop_elements: Optional[Reference] = None
    values_block = getattr(states, "values", []) or []
    for item in values_block:
        if (
            getattr(item, "step_name", None) == "GR"
            and getattr(item, "reference", None) is not None
        ):
            to_loop_elements = item.reference
            break
    if to_loop_elements is None:
        logger.warning(
            "[LR] No to-loop elements found in states.values for step 'GR'. Skipping."
        )
        return states

    # 3) Prepare workspace
    if not hasattr(states, "workspace") or getattr(states, "workspace") is None:
        setattr(states, "workspace", {})
    workspace = getattr(states, "workspace")
    logger.debug(f"[LR Step 3]")
    log_workspace_details(workspace, logger)

    # 4) Current loop base element from context (if any)
    current_loop_base_context_item = None
    context_block = getattr(states, "context", []) or []
    for ctx in context_block:
        concept_info = getattr(ctx, "concept", None)
        concept_name = getattr(concept_info, "name", None)
        if concept_name == current_loop_base_concept_name:
            current_loop_base_context_item = ctx
            logger.debug(
                f"[LR Step 4] Found current loop base element in context: {current_loop_base_context_item}"
            )
            break

    current_loop_base_element_opt = None
    if current_loop_base_context_item is not None:
        current_loop_base_element_opt = getattr(
            current_loop_base_context_item, "reference", None
        )

    # 5) Determine current concept element from function block (first available reference)
    current_concept_element_opt = None
    function_block = getattr(states, "function", []) or []
    for fn in function_block:
        ref = getattr(fn, "reference", None)
        if ref is not None:
            current_concept_element_opt = ref
            break

    logger.debug(
        f"[LR Step 5] From function (inner step result): current_concept_element_opt = {current_concept_element_opt.tensor if current_concept_element_opt else 'None'}"
        f"current_loop_base_element_opt = {current_loop_base_element_opt.tensor if current_loop_base_element_opt else 'None'}"
    )
    # 6) Initialize looper and retrieve next element
    looper = Looper(
        workspace=workspace,
        loop_base_concept_name=loop_base_concept_name,
        loop_concept_index=loop_index,
    )
    (
        next_current_loop_base_element_opt,
        _,
    ) = looper.retrieve_next_base_element(
        to_loop_element_reference=to_loop_elements,
        current_loop_base_element=current_loop_base_element_opt,
    )

    logger.debug(
        f"[LR Step 6] Retrieved next element to loop: next_current_loop_base_element_opt = {next_current_loop_base_element_opt.tensor if next_current_loop_base_element_opt else 'None'}"
    )

    # 7) Decide if current loop base element is new
    is_new = False
    if current_loop_base_element_opt is not None and isinstance(
        current_loop_base_element_opt, Reference
    ):
        is_new_check_result = (
            looper._check_new_base_element_by_looped_base_element(
                current_looped_element_reference=current_loop_base_element_opt,
            )
        )
        logger.debug(
            f"[LR Step 7] Checking if '{current_loop_base_element_opt.tensor if current_loop_base_element_opt else 'None'}' is a new base element. Result: {is_new_check_result}"
        )

        if is_new_check_result:
            is_new = True
            current_loop_base_element = current_loop_base_element_opt
            logger.debug(
                f"[LR Step 7] Element IS new. Assigning inner step result to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}"
            )
        else:
            current_loop_base_element = next_current_loop_base_element_opt
            logger.debug(
                f"[LR Step 7] Element is NOT new. Assigning next element to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}"
            )
    else:
        current_loop_base_element = next_current_loop_base_element_opt
        logger.debug(
            f"[LR Step 7] No inner step result. Assigning next element to current_loop_base_element: {current_loop_base_element.tensor if current_loop_base_element else 'None'}"
        )

    # Store is_loop_progress as an attribute of states
    setattr(states, "is_loop_progress", is_new)
    logger.debug(
        f"[LR Step 7] Stored is_loop_progress attribute: {is_new}"
    )

    # 8) Ensure references
    next_current_loop_base_element = _ensure_reference(
        next_current_loop_base_element_opt
    )
    current_concept_element = _ensure_reference(current_concept_element_opt)
    current_loop_base_element = _ensure_reference(current_loop_base_element)

    # 9) On new element, store base and in-loop concept, but only if they have valid references.
    if is_new:
        if not looper._is_reference_empty(current_loop_base_element):
            # First, create the entry for the new base element and get its loop index.
            logger.debug(
                f"[LR Step 9] Storing NEW base element: {current_loop_base_element.tensor}"
            )
            loop_idx = looper.store_new_base_element(
                current_loop_base_element
            )

            # Now, safely store the inferred concept using the obtained index.
            if not looper._is_reference_empty(current_concept_element):
                logger.debug(
                    f"[LR Step 9] Storing in-loop element '{concept_to_infer_name}' with value {current_concept_element.tensor} for base {current_loop_base_element.tensor} at index {loop_idx}"
                )
                looper.store_new_in_loop_element(
                    current_loop_base_element,
                    concept_to_infer_name,
                    current_concept_element,
                )

    # 10) Update context: Create new 'LR' step records for the inner loop's context.
    new_lr_context_records = []
    for ctx in context_block:
        concept_info = getattr(ctx, "concept", None)
        ctx_name = getattr(concept_info, "name", None)
        new_ref_for_lr = None

        # Determine the new reference for the loop base concept
        if ctx_name == current_loop_base_concept_name:
            new_ref_for_lr = next_current_loop_base_element.copy()

        # Determine the new reference for any in-loop concepts to be carried over
        elif (
            resolved_in_loop_concepts and ctx_name in resolved_in_loop_concepts
        ):
            if not isinstance(ctx_name, str):
                continue

            # For new elements, store the initial value of the in-loop concept (e.g., initial partial_sum).
            if is_new and not looper._is_reference_empty(
                current_loop_base_element
            ):
                looper.store_new_in_loop_element(
                    current_loop_base_element,
                    ctx_name,
                    _ensure_reference(getattr(ctx, "reference", None)),
                )
            carry_index = resolved_in_loop_concepts[ctx_name]["carry_over"]
            initial_ref = _ensure_reference(getattr(ctx, "reference", None))
            new_ref_for_lr = looper.retrieve_next_in_loop_element(
                ctx_name,
                current_loop_index=carry_index,
                initial_reference=initial_ref,
            )

        # If an updated reference was created, add it to our list for the new LR context.
        if new_ref_for_lr:
            new_lr_context_records.append(
                ReferenceRecordLite(
                    step_name="LR",
                    concept=ctx.concept,
                    reference=new_ref_for_lr,
                )
            )

    # Prepend the new LR records to the list so they are found first. The original IR records are preserved.
    states.context = new_lr_context_records + states.context

    # 11) Combine all stored references for the inferred concept
    combined_reference: Optional[Reference] = None
    if is_new:
        combined_reference = (
            looper.combine_all_looped_elements_by_concept(
                to_loop_element_reference=to_loop_elements,
                concept_name=concept_to_infer_name,
                axis_name=concept_to_infer_name,
            )
        )
        if combined_reference is not None:
            # --- Semantic Axis Renaming ---
            loop_base_ref_axes = []
            for v in values_block:
                ci = getattr(v, "concept", None)
                if v.step_name == "IR" and ci and ci.name == loop_base_concept_name:
                    ref = getattr(v, "reference", None)
                    if ref:
                        loop_base_ref_axes = ref.axes
                        break

            current_axes = combined_reference.axes.copy()
            final_axes = current_axes

            if current_axes and loop_base_ref_axes:
                final_axes[0] = loop_base_ref_axes[0]
                final_axes = [ 'value' if ax == '_none_axis' else ax for ax in final_axes]
                
                if len(final_axes) == len(set(final_axes)):
                    combined_reference.axes = final_axes

    # 12) Write result into states.inference under LR if the entry exists
    if combined_reference is not None:
        for inf in getattr(states, "inference", []) or []:
            if getattr(inf, "step_name", None) == "LR":
                setattr(inf, "reference", combined_reference)
                break

    states.set_current_step("LR")
    logger.debug("LR completed.")
    return states

