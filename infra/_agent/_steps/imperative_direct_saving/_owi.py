import logging

from infra._states._imperative_states import States


def output_working_interpretation(states: States) -> States:
    """No-op finalization for demo."""
    states.set_current_step("OWI")
    logging.debug("OWI completed.")
    return states 