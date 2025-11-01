from typing import Callable
import logging

from infra._states._judgement_direct_states import States
from infra._core import cross_action

logging.basicConfig(level=logging.DEBUG)

def tool_value_actuation(states: States) -> States:
    """Apply the function from MFP to the values from MVP."""
    func_ref = states.get_reference("function", "MFP")
    values_ref = states.get_reference("values", "MVP")

    if func_ref and values_ref:
        # The function is stored as a callable in the reference tensor
        axis_name = func_ref.axes[0]
        func_callable = func_ref.get(**{axis_name: 0})
        if func_callable and isinstance(func_callable, Callable):
            # Wrap the generation function to ensure its output is a list,
            # as required by the `cross_action` function.
            def _list_wrapper_fn(*args, **kwargs):
                result = func_callable(*args, **kwargs)
                return result if isinstance(result, list) else [result]

            # Create a new reference for the wrapped function to avoid side effects.
            wrapped_func_ref = func_ref.copy()
            wrapped_func_ref.set(_list_wrapper_fn, **{axis_name: 0})

            # Determine the name for the new axis from the inference concept.
            inference_record = states.get_first_record("inference", "IR")
            new_axis_name = "result"
            if inference_record and inference_record.concept and inference_record.concept.axis_name:
                new_axis_name = inference_record.concept.axis_name

            applied_ref = cross_action(wrapped_func_ref, values_ref, new_axis_name)

            # If the new axis only has a single element, slice it off to simplify the structure.
            final_ref = applied_ref
            try:
                new_axis_index = applied_ref.axes.index(new_axis_name)
                if applied_ref.shape[new_axis_index] == 1:
                    axes_to_keep = [axis for axis in applied_ref.axes if axis != new_axis_name]
                    final_ref = applied_ref.slice(*axes_to_keep)
            except (ValueError, IndexError):
                # If axis not found or shape is inconsistent, proceed without slicing.
                pass

            states.set_reference("inference", "TVA", final_ref)

    states.set_current_step("TVA")
    logging.debug(f"TVA completed. Inference state after actuation: {states.inference}")
    return states
