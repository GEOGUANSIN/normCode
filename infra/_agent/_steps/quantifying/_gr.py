import logging
from infra._states._quantifying_states import States
from infra._syntax._grouper import Grouper
from infra._states._common_states import ReferenceRecordLite


def grouping_references(states: States) -> States:
    """Perform the core grouping logic for quantification."""
    # 1. Get value references to be grouped.
    value_refs = [r.reference.copy() for r in states.values if r.reference and r.step_name == "IR"]
    if not value_refs:
        logging.warning("[GR] No value references found for grouping.")
        states.set_current_step("GR")
        return states

    # 2. Find the axis of the concept we are grouping over from the value concepts.
    group_base_concept_name = getattr(states.syntax, "group_base", None)
    loop_base_axis = None
    if group_base_concept_name:
        loop_base_axis = next(
            (
                r.concept.axis_name
                for r in states.values
                if r.concept and r.concept.name == group_base_concept_name
            ),
            None,
        )

    if not loop_base_axis and value_refs[0].axes:
        loop_base_axis = value_refs[0].axes[0]
        logging.warning(
            f"Loop base axis not found for '{group_base_concept_name}'. Falling back to '{loop_base_axis}'."
        )

    # 3. Perform grouping. For quantification, this is essentially a flattening operation.
    grouper = Grouper()
    # For quantification, we always use or_across pattern
    # Pass a copy of the axes to prevent destructive modification of the original reference.
    by_axes = [[loop_base_axis] if loop_base_axis else ref.axes.copy() for ref in value_refs]
    to_loop_ref = grouper.or_across(
        references=value_refs,
        by_axes=by_axes,
    )

    current_loop_base_concept_name = (
        f"{getattr(states.syntax, 'LoopBaseConcept', None)}*"
        if getattr(states.syntax, "LoopBaseConcept", None)
        else None
    )
    # Safely get the axis name from the concept, not the reference.
    current_loop_base_concept_axis = next(
        (
            r.concept.axis_name
            for r in states.context
            if r.concept and r.concept.name == current_loop_base_concept_name
        ),
        None,
    )

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