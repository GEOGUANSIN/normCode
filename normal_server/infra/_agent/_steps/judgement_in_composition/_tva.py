from typing import Callable
import logging

from infra._states._judgement_states import States
from infra._core import cross_action

logging.basicConfig(level=logging.DEBUG)

def tool_value_actuation(states: States) -> States:
    """Apply the function from MFP to the values from MVP."""
    func_ref = states.get_reference("function", "MFP")
    values_ref = states.get_reference("values", "MVP")

    # Retrieve the flag, default to True to maintain backward compatibility
    create_axis = getattr(states, "create_axis_on_list_output", True)

    # Handle case where there are no input values (e.g., blocking read operations)
    # The composed function still needs to be called with an empty dict
    if func_ref and not values_ref:
        axis_name = func_ref.axes[0]
        func_callable = func_ref.get(**{axis_name: 0})
        if func_callable and isinstance(func_callable, Callable):
            logging.debug("TVA: No values_ref - calling function with empty dict (blocking read case)")
            # Call the composed function with an empty input dict
            result = func_callable({})
            
            # Create a reference for the result
            from infra._core import Reference
            final_ref = Reference(
                axes=["_none_axis"],
                shape=(1,),
                skip_value="@#SKIP#@"
            )
            final_ref._replace_data([result])
            states.set_reference("inference", "TVA", final_ref)
            logging.debug(f"TVA: Blocking call completed with result: {type(result)}")
    elif func_ref and values_ref:
        # The function is stored as a callable in the reference tensor
        axis_name = func_ref.axes[0]
        func_callable = func_ref.get(**{axis_name: 0})
        if func_callable and isinstance(func_callable, Callable):
            # Wrap the generation function to ensure its output is a list,
            # as required by the `cross_action` function.
            def _list_wrapper_fn(*args, **kwargs):
                result = func_callable(*args, **kwargs)
                
                if create_axis:
                    # Original behavior: ensure it's a list to create an axis
                    return result if isinstance(result, list) else [result]
                else:
                    # New behavior: wrap in a single-element list to avoid axis explosion
                    # cross_action expects a list of results, so [result] means "one result"
                    # regardless of whether 'result' is a list or an object.
                    return [result]

            # Create a new reference for the wrapped function to avoid side effects.
            wrapped_func_ref = func_ref.copy()
            wrapped_func_ref.set(_list_wrapper_fn, **{axis_name: 0})

            # Determine the name for the new axis from the inference concept.
            inference_record = states.get_first_record("inference", "IR")
            new_axis_name = "result"
            if inference_record and inference_record.concept and inference_record.concept.axis_name:
                new_axis_name = inference_record.concept.axis_name

            applied_ref = cross_action(wrapped_func_ref, values_ref, new_axis_name)

            # If the new axis only has a single element, collapse it to simplify the structure.
            # We need to properly extract the single element, not just slice to fewer axes.
            final_ref = applied_ref
            try:
                new_axis_index = applied_ref.axes.index(new_axis_name)
                if applied_ref.shape[new_axis_index] == 1:
                    # Properly collapse the singleton result axis by extracting element at index 0
                    # This removes the extra nesting that would otherwise remain
                    axes_to_keep = [axis for axis in applied_ref.axes if axis != new_axis_name]
                    if axes_to_keep:
                        # Slice to the remaining axes and collapse the result axis
                        sliced_ref = applied_ref.slice(*axes_to_keep)
                        # The sliced data still contains the result axis nesting - unwrap it
                        def unwrap_singleton_axis(data, depth, target_depth):
                            """Recursively unwrap the singleton result axis from data."""
                            if depth >= target_depth:
                                # At the result axis level - extract index 0
                                if isinstance(data, list) and len(data) == 1:
                                    return data[0]
                                return data
                            if isinstance(data, list):
                                return [unwrap_singleton_axis(item, depth + 1, target_depth) for item in data]
                            return data
                        
                        # The result axis was at new_axis_index, unwrap at that depth
                        from infra._core import Reference
                        unwrapped_data = unwrap_singleton_axis(sliced_ref.tensor, 0, len(axes_to_keep))
                        final_ref = Reference(
                            axes=sliced_ref.axes.copy(),
                            shape=sliced_ref.shape,
                            skip_value=sliced_ref.skip_value
                        )
                        final_ref._replace_data(unwrapped_data)
                    else:
                        # No other axes - extract the single scalar value
                        from infra._core import Reference
                        scalar_value = applied_ref.tensor
                        while isinstance(scalar_value, list) and len(scalar_value) == 1:
                            scalar_value = scalar_value[0]
                        final_ref = Reference(
                            axes=["_none_axis"],
                            shape=(1,),
                            skip_value=applied_ref.skip_value
                        )
                        final_ref._replace_data([scalar_value])
            except (ValueError, IndexError):
                # If axis not found or shape is inconsistent, proceed without collapsing.
                pass

            states.set_reference("inference", "TVA", final_ref)

    states.set_current_step("TVA")
    logging.debug(f"TVA completed. Full inference state before exit: {[r.step_name for r in states.inference]}")
    return states 