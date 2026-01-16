import logging

from infra._states._imperative_states import States


def output_reference(states: States) -> States:
    """Finalize the output reference."""
    mia_ref = states.get_reference("inference", "MIA")
    if mia_ref:
        states.set_reference("inference", "OR", mia_ref)
    states.set_current_step("OR")
    logging.debug(f"OR completed. Final inference state: {states.inference}")
    return states
