import logging
from infra._states._assigning_states import States


def output_reference(states: States) -> States:
    """Finalize the output reference."""
    ar_ref = states.get_reference("inference", "AR")
    if ar_ref:
        states.set_reference("inference", "OR", ar_ref)
    states.set_current_step("OR")
    logging.debug("OR completed.")
    return states 