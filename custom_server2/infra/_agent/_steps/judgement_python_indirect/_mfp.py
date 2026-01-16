from types import SimpleNamespace
import logging
from copy import deepcopy

from infra._states._imperative_states import States
from infra._core._reference import Reference, element_action
from infra._agent._models._model_runner import ModelSequenceRunner

logging.basicConfig(level=logging.DEBUG)


def model_function_perception(states: States) -> States:
    """
    Vectorize the model function perception step.
    Applies the generation plan from IWI to each instruction in the function_concept's reference.
    """
    sequence_spec = states.mfp_sequence_spec
    if not sequence_spec:
        logging.warning("MFP: No sequence spec found in states. Skipping.")
        states.set_current_step("MFP")
        return states

    ir_func_record = next((f for f in states.function if f.step_name == "IR"), None)
    if not ir_func_record or not ir_func_record.reference:
        logging.warning("MFP: No function reference found from IR step. Skipping.")
        states.set_current_step("MFP")
        return states

    class _MfpStateProxy:
        def __init__(self, s: States, instruction_name_override: str):
            self.body = s.body

            # Create a copy of the original concept and override its name
            # This is the key to making the generic plan from IWI work for a specific instruction
            original_concept_info = deepcopy(ir_func_record.concept)
            original_concept_info.name = instruction_name_override
            self.function = SimpleNamespace(concept=original_concept_info)

            # Inference concept remains the same for context
            ir_inference_record = next((r for r in s.inference if r.step_name == "IR"), None)
            ir_inference_concept = ir_inference_record.concept if ir_inference_record else None
            self.inference = SimpleNamespace(concept=ir_inference_concept)

    def _generate_for_one_instruction(instruction: str):
        """Wrapper function to run the ModelSequenceRunner for a single instruction string."""
        if not isinstance(instruction, str):
            return None  # Handle skip values or other non-string data in the reference

        logging.debug(f"MFP: Generating function for instruction: '{instruction}'")
        # Create a specialized proxy with the current instruction name
        proxy = _MfpStateProxy(states, instruction_name_override=instruction)
        
        # Run the sequence defined in IWI using the specialized proxy
        meta = ModelSequenceRunner(proxy, sequence_spec).run()
        
        # The result is the callable function
        instruction_fn = meta.get("instruction_fn")
        if not instruction_fn:
            logging.error(f"MFP: Failed to generate instruction_fn for: '{instruction}'")
            return None
        return instruction_fn

    instruction_reference = ir_func_record.reference

    # Use element_action to apply the generation function to each instruction in the reference
    function_reference = element_action(
        f=_generate_for_one_instruction,
        references=[instruction_reference]
    )

    states.set_reference("function", "MFP", function_reference)

    states.set_current_step("MFP")
    logging.debug(f"MFP completed. Function state after model run: {states.function}")
    return states 