import logging
from infra._core._inference import Inference
from infra._states._timing_states import States
from infra._syntax import Timer

logger = logging.getLogger(__name__)


def timing(states: States) -> States:
    """Check if timing conditions are met and execute if conditions are satisfied."""
    marker = states.syntax.marker
    condition = states.syntax.condition
    
    if not states.blackboard:
        logger.error("Blackboard not found in states. Cannot perform timing check.")
        states.set_current_step("T")
        raise ValueError("Blackboard not found in states. Cannot perform timing check.")
        return states
        
    timer = Timer(states.blackboard)
    
    states.timing_ready = False  # Default to not ready
    
    # Check if conditions are met based on marker type
    if marker == "after":
        if timer.check_progress_condition(condition):
            states.timing_ready = True
        logger.info(f"@after condition '{condition}' met: {states.timing_ready}")

    elif marker == "if":
        is_ready, to_be_skipped = timer.check_if_condition(condition)
        if is_ready:
            states.timing_ready = True
            if to_be_skipped:
                states.to_be_skipped = True

    else:
        logger.warning(f"Unknown or unsupported timing marker: {marker}")
    
    # Log outcome
    if states.timing_ready:
        if states.to_be_skipped:
            logger.info(f"Timing condition '{condition}' resulted in a skip.")
        else:
            logger.info(f"Timing conditions met for '{condition}' - proceeding with execution.")
    else:
        logger.info(f"Timing conditions not met for '{condition}', pending execution.")
    
    states.set_current_step("T")
    return states 