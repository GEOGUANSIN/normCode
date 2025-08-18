import logging
from infra._states._grouping_states import States
from infra._core._reference import Reference
from infra._syntax._grouper import Grouper


def grouping_references(states: States) -> States:
    """Perform the core grouping logic."""
    context_refs = [r.reference for r in states.context if r.reference]
    value_refs = [r.reference for r in states.values if r.reference]
    value_concept_names = [c.concept.name for c in states.values if c.concept]

    by_axes = [ref.axes for ref in context_refs]

    grouper = Grouper()
    result_ref = None

    if states.syntax.marker == "in":
        logging.debug(f"Performing 'and_in' grouping with by_axes: {by_axes}")
        result_ref = grouper.and_in(
            value_refs,
            value_concept_names,
            by_axes=by_axes,
        )
    elif states.syntax.marker == "across":
        logging.debug(f"Performing 'or_across' grouping with by_axes: {by_axes}")
        result_ref = grouper.or_across(
            value_refs,
            by_axes=by_axes,
        )
    else:
        logging.warning(f"No valid grouping marker found ('{states.syntax.marker}'). Skipping grouping.")
        # Create an empty reference to avoid errors downstream
        result_ref = Reference(axes=["result"], shape=(0,))

    if result_ref:
        states.set_reference("inference", "GR", result_ref)

    states.set_current_step("GR")
    logging.debug("GR completed.")
    return states 