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

    # Find the source and destination records from the values list
    value_concepts_map = {rec.concept.name: rec for rec in states.values}

    source_record = value_concepts_map.get(assign_source_name)
    dest_record = value_concepts_map.get(assign_destination_name)

    if not source_record or not dest_record:
        logging.error(f"AR failed: Could not find concepts '{assign_source_name}' or '{assign_destination_name}' in value concepts.")
        states.set_current_step("AR")
        return states

    source_ref = source_record.reference
    dest_ref = dest_record.reference
    
    assigner = Assigner()
    output_ref = None

    if syntax_marker == ".":  # Specification
        logging.info(f"Performing specification (.): Assigning '{source_record.concept.name}' reference to '{dest_record.concept.name}'.")
        output_ref = assigner.specification(source_ref, dest_ref)

    elif syntax_marker == "+":  # Continuation
        logging.info(f"Performing continuation (+): Adding '{source_record.concept.name}' reference to '{dest_record.concept.name}'.")
        output_ref = assigner.continuation(source_ref, dest_ref)

    else:
        logging.warning(f"Unknown syntax marker: {syntax_marker}. No assignment performed.")
        # If no operation, the output is just the destination's original reference
        if dest_ref:
            output_ref = dest_ref.copy()

    if output_ref:
        states.set_reference("inference", "AR", output_ref)

    states.set_current_step("AR")
    logging.debug(f"AR completed. Output reference: {output_ref.get() if output_ref else None}")
    return states 