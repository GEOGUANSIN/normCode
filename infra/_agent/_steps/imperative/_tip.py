import logging

from infra._states._imperative_states import States


def tool_inference_perception(states: States) -> States:
    """Pass-through from TVA for this demo."""
    tva_ref = states.get_reference("inference", "TVA")
    if tva_ref:
        states.set_reference("inference", "TIP", tva_ref)
    states.set_current_step("TIP")
    logging.debug(f"TIP completed. Inference state: {states.inference}")
    return states 