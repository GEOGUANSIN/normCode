from infra._states._simple_states import States


def output_working_interpretation(states: States) -> States:
    """No-op finalization for simple demo."""
    states.set_current_step("OWI")
    return states 