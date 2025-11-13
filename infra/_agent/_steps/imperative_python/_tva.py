from typing import Callable
import logging

from infra._states._imperative_states import States
from infra._core import cross_action, element_action

logging.basicConfig(level=logging.DEBUG)

def tool_value_actuation(states: States) -> States:
    """Apply the function from MFP to the values from MVP."""
    func_ref = states.get_reference("function", "MFP")
    values_ref = states.get_reference("values", "MVP")

    if func_ref and values_ref:
        # Define a wrapper that ensures any callable's output is a list,
        # as required by cross_action.
        def _list_wrapper_fn(func: Callable | None) -> Callable | None:
            if not func or not isinstance(func, Callable):
                return None  # Pass through non-callables (like skip values)

            def wrapped(*args, **kwargs):
                result = func(*args, **kwargs)
                # Ensure the final result is always a list for cross_action compatibility
                return result if isinstance(result, list) else [result]
            return wrapped

        # Apply the wrapper to every function in the function reference tensor.
        wrapped_func_ref = element_action(_list_wrapper_fn, [func_ref])

        # Determine the name for the new axis from the inference concept.
        inference_record = states.get_first_record("inference", "IR")
        new_axis_name = "result"
        if inference_record and inference_record.concept and inference_record.concept.axis_name:
            new_axis_name = inference_record.concept.axis_name

        # The cross_action will now correctly apply each function to the broadcasted values.
        applied_ref = cross_action(wrapped_func_ref, values_ref, new_axis_name)

        # Post-processing to simplify the output structure if possible.
        final_ref = applied_ref
        try:
            new_axis_index = applied_ref.axes.index(new_axis_name)
            if applied_ref.shape[new_axis_index] == 1:
                axes_to_keep = [axis for axis in applied_ref.axes if axis != new_axis_name]
                final_ref = applied_ref.slice(*axes_to_keep)
        except (ValueError, IndexError):
            pass

        states.set_reference("inference", "TVA", final_ref)

    states.set_current_step("TVA")
    logging.debug(f"TVA completed. Inference state after actuation: {states.inference}")
    return states 