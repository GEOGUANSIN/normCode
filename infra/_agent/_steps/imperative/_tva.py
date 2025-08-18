from typing import Callable
import logging

from infra._states._imperative_states import States
from infra._core import cross_action


def tool_value_actuation(states: States) -> States:
    """Apply the function from MFP to the values from MVP."""
    func_ref = states.get_reference("function", "MFP")
    values_ref = states.get_reference("values", "MVP")

    if func_ref and values_ref:
        # The function is stored as a callable in the reference tensor
        func_callable = func_ref.get(f=0)
        if func_callable and isinstance(func_callable, Callable):
            # Wrap the generation function to ensure its output is a list,
            # as required by the `cross_action` function.
            def _list_wrapper_fn(*args, **kwargs):
                result = func_callable(*args, **kwargs)
                return result if isinstance(result, list) else [result]

            # Create a new reference for the wrapped function to avoid side effects.
            wrapped_func_ref = func_ref.copy()
            wrapped_func_ref.set(_list_wrapper_fn, f=0)

            applied_ref = cross_action(wrapped_func_ref, values_ref, "result")
            states.set_reference("inference", "TVA", applied_ref)

    states.set_current_step("TVA")
    logging.debug(f"TVA completed. Inference state after actuation: {states.inference}")
    return states 