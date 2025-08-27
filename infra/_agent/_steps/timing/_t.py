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
    
    condition_met = False
    # Check if conditions are met based on marker type
    if marker == "after":
        condition_met = timer.check_progress_condition(condition)
        logger.info(f"@after condition '{condition}' met: {condition_met}")
    else:
        logger.warning(f"Unknown or unsupported timing marker: {marker}")
    
    # Execute if conditions are met
    if condition_met:
        logger.info(f"Conditions met - proceeding with execution")
        states.timing_ready = True
    else:
        logger.info("Conditions not met, skipping execution")
    
    states.set_current_step("T")
    return states 