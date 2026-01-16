import logging
from infra._states._looping_states import States
from infra._states._common_states import ReferenceRecordLite


def output_reference(states: States) -> States:
    """Finalize the output reference and context from the LR step."""
    # The final result is the one produced by the LR step.
    lr_ref = states.get_reference("inference", "LR")
    if lr_ref:
        states.set_reference("inference", "OR", lr_ref)

    # Copy LR context records to be the new OR context records for the next iteration.
    or_context_records = [
        ReferenceRecordLite(
            step_name="OR",
            concept=ctx.concept,
            reference=ctx.reference.copy() if ctx.reference else None,
        )
        for ctx in states.context
        if ctx.step_name == "LR"
    ]

    # Keep all non-OR records and add the new OR records.
    non_or_context = [c for c in states.context if c.step_name != "OR"]
    states.context = or_context_records + non_or_context

    states.set_current_step("OR")
    logging.debug("OR completed.")
    return states
