import logging

from infra._core import Reference
from infra._states._imperative_states import States

logging.basicConfig(level=logging.DEBUG)


def _check_all_match(data, condition):
    if isinstance(data, list):
        return all(_check_all_match(item, condition) for item in data)
    else:
        return data == condition


def tool_inference_perception(states: States) -> States:
    """
    Checks the tensor data from TVA against a condition.
    If all elements match the condition, sets a reference indicating success ([$(T)%_]).
    Otherwise, sets a reference indicating failure ([$(F)%_]).
    If no condition is provided, it acts as a pass-through from TVA.
    """
    tva_ref = states.get_reference("inference", "TVA")
    condition = getattr(states, "condition", None)

    if tva_ref and condition is not None:
        tensor_data = tva_ref.tensor

        if tensor_data is None:
            all_match = False
        else:
            # The result from a python script might be a list with one item
            if isinstance(tensor_data, list) and len(tensor_data) == 1:
                tensor_data = tensor_data[0]
            all_match = _check_all_match(tensor_data, condition)

        states.condition_met = all_match
        logging.debug(f"TIP condition met: {all_match}")

        if all_match:
            tip_ref = Reference.from_data(["$(T)%"], axis_names=['condition_met'])
        else:
            tip_ref = Reference.from_data(["$(F)%"], axis_names=['condition_met'])
        states.set_reference("inference", "TIP", tip_ref)

    elif tva_ref:
        # Pass-through if no condition
        states.set_reference("inference", "TIP", tva_ref)

    states.set_current_step("TIP")
    logging.debug(f"TIP completed. Inference state: {states.inference}")
    return states 