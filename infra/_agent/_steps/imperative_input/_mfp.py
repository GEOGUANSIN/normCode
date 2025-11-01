from types import SimpleNamespace
import logging

from infra._states._imperative_states import States
from infra._core._reference import Reference
from infra._agent._models._model_runner import ModelSequenceRunner

logging.basicConfig(level=logging.DEBUG)


def model_function_perception(states: States) -> States:
    """
    Execute a model sequence to create a user input function.
    Uses the affordance system to create a function that prompts the user.
    """
    # Specs and body are now retrieved from the states object, prepared during IWI.
    sequence_spec = states.mfp_sequence_spec

    # The `ModelSequenceRunner` needs an object with `body` and `function` attributes.
    # We create a temporary proxy that pulls these from our `States` object for clarity.
    class _MfpStateProxy:
        def __init__(self, s: States):
            self.body = s.body

            ir_func_record = next((f for f in s.function if f.step_name == "IR"), None)
            ir_func_concept = ir_func_record.concept if ir_func_record else None
            self.function = SimpleNamespace(concept=ir_func_concept)

            ir_inference_record = next((r for r in s.inference if r.step_name == "IR"), None)
            ir_inference_concept = ir_inference_record.concept if ir_inference_record else None
            self.inference = SimpleNamespace(concept=ir_inference_concept)

    mfp_states_proxy = _MfpStateProxy(states)

    ir_func_record = next((f for f in states.function if f.step_name == "IR"), None)

    # Run the sequence to create the input function
    if sequence_spec:
        meta = ModelSequenceRunner(mfp_states_proxy, sequence_spec).run()
        # The result of MFP is a callable function. We wrap it in a Reference.
        input_fn = meta.get("input_fn")  # This key comes from your sequence spec
        if input_fn:
            axis_name = ir_func_record.reference.axes[0] if ir_func_record and ir_func_record.reference else "f"
            ref = Reference(axes=[axis_name], shape=(1,))
            ref.set(input_fn, **{axis_name: 0})
            states.set_reference("function", "MFP", ref)

    states.set_current_step("MFP")
    logging.debug(f"MFP completed. Function state after creating input function: {states.function}")
    return states