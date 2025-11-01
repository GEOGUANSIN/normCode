from typing import Any
import logging
import uuid

from infra._states._judgement_direct_states import States
from infra._core import element_action

logging.basicConfig(level=logging.DEBUG)

def memory_inference_actuation(states: States) -> States:
    """Wrap the result in the normcode wrapper %...()."""
    tip_ref = states.get_reference("inference", "TIP")
    if tip_ref:

        def wrap_element(element: Any) -> Any:
            # The element from cross_action is a list; we want to wrap the first item.
            value_to_wrap = element[0] if isinstance(element, list) and element else element
            unique_code = uuid.uuid4().hex[:3]
            return f"%{unique_code}({value_to_wrap})"

        wrapped_ref = element_action(wrap_element, [tip_ref])
        states.set_reference("inference", "MIA", wrapped_ref)

    states.set_current_step("MIA")
    logging.debug(f"MIA completed. Inference state after wrapping: {states.inference}")
    return states
