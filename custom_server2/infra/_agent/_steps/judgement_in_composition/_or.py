from __future__ import annotations
from typing import TYPE_CHECKING
from infra._states._judgement_states import States
import logging

if TYPE_CHECKING:
    from infra import Inference


def output_reference(inference: "Inference", states: States) -> States:
    """
    Assigns the final result from the TIA step to the concept_to_infer.
    
    The sequence is: TVA → TIA → OR
    TIA produces the truth mask (with assertion applied), which is the final output.
    """
    logging.debug(f"OR started. Full inference state at entry: {[r.step_name for r in states.inference]}")
    
    # First try to get result from TIA (which comes after TVA)
    tia_record = next((r for r in states.inference if r.step_name == "TIA"), None)
    
    if tia_record and tia_record.reference:
        logging.debug(f"OR: Found result from TIA (truth mask), assigning to concept_to_infer.")
        final_ref = tia_record.reference
        inference.concept_to_infer.reference = final_ref
        states.set_reference("inference", "OR", final_ref)
    else:
        # Fallback to TVA if TIA didn't produce a result (shouldn't happen)
        logging.warning("OR: No result from TIA, falling back to TVA.")
        tva_record = next((r for r in states.inference if r.step_name == "TVA"), None)
        if tva_record and tva_record.reference:
            final_ref = tva_record.reference
            inference.concept_to_infer.reference = final_ref
            states.set_reference("inference", "OR", final_ref)
        else:
            logging.error("OR: No result found from TIA or TVA step to output.")

    states.set_current_step("OR")
    logging.debug(f"OR completed. Final inference state: {inference.concept_to_infer.reference}")
    return states 