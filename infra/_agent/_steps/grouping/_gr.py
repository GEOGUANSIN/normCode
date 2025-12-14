import logging
from infra._states._grouping_states import States
from infra._core._reference import Reference
from infra._syntax._grouper import Grouper


def grouping_references(states: States) -> States:
    """Perform the core grouping logic."""
    by_axis_concepts = getattr(states.syntax, 'by_axis_concepts', None)
    # New: per-reference axes (List[List[str]]) and create_axis
    per_ref_by_axes = getattr(states.syntax, 'by_axes', None)
    create_axis = getattr(states.syntax, 'create_axis', None)

    if by_axis_concepts:
        context_refs = [
            r.reference for r in states.context
            if r.reference and r.concept and r.concept.name in by_axis_concepts
        ]
    else:
        context_refs = [r.reference for r in states.context if r.reference]

    value_refs = [r.reference for r in states.values if r.reference]
    value_concept_names = [c.concept.name for c in states.values if c.concept]

    # Legacy: derive by_axes from context concepts (flat list)
    by_axes_lists = [ref.axes for ref in context_refs]
    legacy_by_axes = list(dict.fromkeys([axis for sublist in by_axes_lists for axis in sublist]))
    protect_axes = getattr(states.syntax, 'protect_axes', None)
    if protect_axes:
        legacy_by_axes = [axis for axis in legacy_by_axes if axis not in protect_axes]

    # Determine which by_axes to use
    if per_ref_by_axes is not None:
        by_axes_for_grouper = per_ref_by_axes  # List[List[str]]
        logging.debug(f"Using per-ref by_axes: {by_axes_for_grouper}, create_axis: {create_axis}")
    else:
        by_axes_for_grouper = legacy_by_axes  # List[str]
        logging.debug(f"Using legacy by_axes: {by_axes_for_grouper}")

    grouper = Grouper()
    result_ref = None

    if states.syntax.marker == "in":
        logging.debug(f"Performing 'and_in' grouping, removing by_axes: {legacy_by_axes}")
        result_ref = grouper.and_in(
            value_refs,
            value_concept_names,
            by_axes=legacy_by_axes,
        )
    elif states.syntax.marker == "across":
        logging.debug(f"Performing 'or_across' grouping")
        result_ref = grouper.or_across(
            value_refs,
            by_axes=by_axes_for_grouper,
            create_axis=create_axis,
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