import logging
from infra._states._quantifying_states import States
from infra._syntax._quantifier import Quantifier

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def output_working_interpretation(states: States) -> States:
    """Check for loop completion and set status."""

    syntax_data = getattr(states, "syntax", {})
    loop_base_concept_name = getattr(syntax_data, "LoopBaseConcept", None)

    to_loop_elements = None
    values_block = getattr(states, "values", []) or []
    for item in values_block:
        if getattr(item, "step_name", None) == "GR" and getattr(item, "reference", None) is not None:
            to_loop_elements = item.reference
            break

    is_complete = False
    logger.debug(
        f"[OWI Step 1] Checking if loop is complete. Loop base concept name: {loop_base_concept_name}, To loop elements: {to_loop_elements}"
    )
    if loop_base_concept_name and to_loop_elements:
        quantifier_index = getattr(syntax_data, "quantifier_index", 0)
        quantifier = Quantifier(
            workspace=states.workspace,
            loop_base_concept_name=loop_base_concept_name,
            loop_concept_index=quantifier_index,
        )
        concept_to_infer_name = (getattr(syntax_data, "ConceptToInfer") or [""])[0]
        if quantifier.check_all_base_elements_looped(
            to_loop_elements, in_loop_element_name=concept_to_infer_name
        ):
            is_complete = True

    setattr(states.syntax, "completion_status", is_complete)
    logger.debug(f"[OWI Step 2] Completion status: {is_complete}")

    states.set_current_step("OWI")
    logger.debug(f"OWI completed. Completion status: {is_complete}")
    return states 