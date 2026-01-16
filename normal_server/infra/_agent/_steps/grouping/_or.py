import logging

from infra._states._grouping_states import States


def output_reference(states: States) -> States:
    """Finalize the output reference."""
    gr_ref = states.get_reference("inference", "GR")
    if gr_ref:
        states.set_reference("inference", "OR", gr_ref)
    states.set_current_step("OR")
    logging.debug("OR completed.")
    return states 