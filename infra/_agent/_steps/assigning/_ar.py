import logging
from infra._core import Reference
from infra._states._assigning_states import States
from infra._syntax import Assigner


def assigning_references(states: States) -> States:
    """Perform assignment based on syntax marker."""
    syntax_marker = states.syntax.marker
    assign_source_name = states.syntax.assign_source
    assign_destination_name = states.syntax.assign_destination

    if not assign_source_name or not assign_destination_name:
        logging.error("AR failed: 'assign_source' and 'assign_destination' must be specified in syntax.")
        states.set_current_step("AR")
        return states

    value_concepts_map = {rec.concept.name: rec for rec in states.values}
    dest_record = value_concepts_map.get(assign_destination_name) if assign_destination_name else None
    dest_ref = dest_record.reference if dest_record else None

    assigner = Assigner()
    output_ref = None

    if syntax_marker == ".":  # Specification
        source_refs = []
        if isinstance(assign_source_name, list):
            source_refs = [value_concepts_map.get(name).reference if value_concepts_map.get(name) else None for name in assign_source_name]
            logging.info(f"Performing specification (.) with source candidates: {assign_source_name} for destination '{assign_destination_name}'.")
        else:
            source_record = value_concepts_map.get(assign_source_name)
            if not source_record:
                logging.error(f"AR failed: Could not find source concept '{assign_source_name}' in value concepts.")
                states.set_current_step("AR")
                return states
            source_refs = [source_record.reference]
            logging.info(f"Performing specification (.): Assigning '{assign_source_name}' reference to '{assign_destination_name if assign_destination_name else None}'.")

        output_ref = assigner.specification(source_refs, dest_ref)

    elif syntax_marker == "+":  # Continuation
        if isinstance(assign_source_name, list):
            logging.error(f"AR failed for continuation (+): 'assign_source' must be a single concept, not a list.")
            states.set_current_step("AR")
            return states

        source_record = value_concepts_map.get(assign_source_name)
        if not source_record:
            logging.error(f"AR failed: Could not find source concept '{assign_source_name}' in value concepts.")
            states.set_current_step("AR")
            return states

        source_ref = source_record.reference
        logging.info(f"Performing continuation (+): Adding '{source_record.concept.name}' reference to '{assign_destination_name}'.")
        output_ref = assigner.continuation(source_ref, dest_ref, by_axes=states.syntax.by_axes)

    else:
        logging.warning(f"Unknown syntax marker: {syntax_marker}. No assignment performed.")
        if dest_ref:
            output_ref = dest_ref.copy()

    if output_ref:
        states.set_reference("inference", "AR", output_ref)

    states.set_current_step("AR")
    logging.debug(f"AR completed. Output reference: {output_ref.get() if output_ref else None}")
    return states 