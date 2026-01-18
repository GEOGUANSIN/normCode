from __future__ import annotations
from typing import TYPE_CHECKING
from infra._states._imperative_states import States
import logging

if TYPE_CHECKING:
    from infra import Inference


def output_reference(inference: "Inference", states: States) -> States:
    """
    Assigns the final result from the TVA step to the concept_to_infer.
    """
    logging.debug(f"OR started. Full inference state at entry: {[r.step_name for r in states.inference]}")
    # Find the record produced by the TVA step by iterating through the inference list.
    tva_record = next((r for r in states.inference if r.step_name == "TVA"), None)
    
    if tva_record and tva_record.reference:
        logging.debug(f"OR: Found result from TVA, assigning to concept_to_infer.")
        final_ref = tva_record.reference
        inference.concept_to_infer.reference = final_ref
        states.set_reference("inference", "OR", final_ref)
    else:
        logging.warning("OR: No result found from TVA step to output.")

    states.set_current_step("OR")
    logging.debug(f"OR completed. Final inference state: {inference.concept_to_infer.reference}")
    return states 