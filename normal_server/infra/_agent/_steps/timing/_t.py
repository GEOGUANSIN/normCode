import logging
from typing import Optional
from infra._core._inference import Inference
from infra._states._timing_states import States
from infra._syntax import Timer

logger = logging.getLogger(__name__)


def _get_parent_flow_index(flow_index: Optional[str]) -> Optional[str]:
    """
    Get the parent flow index from a timing inference's flow index.
    
    Example: '1.1.3.1' -> '1.1.3' (timing controls the parent inference)
    """
    if not flow_index:
        return None
    parts = flow_index.split('.')
    if len(parts) <= 1:
        return None
    return '.'.join(parts[:-1])


def _inject_filter_for_parent(states: States, timer: Timer, condition: str) -> None:
    """
    Inject a truth mask filter into the workspace for the parent inference.
    
    When a timing condition passes without skipping, and the condition has a
    truth mask (from a judgement with for-each quantifier), we inject the filter
    into the workspace. The parent inference's IR step can then apply this filter
    to all input references.
    """
    if not states.flow_index or not states.workspace:
        logger.debug("Cannot inject filter: missing flow_index or workspace")
        return
    
    truth_mask_data = timer.get_truth_mask_for_filter(condition)
    if not truth_mask_data:
        logger.debug(f"No truth mask available for condition '{condition}' - no filter to inject")
        return
    
    parent_flow_index = _get_parent_flow_index(states.flow_index)
    if not parent_flow_index:
        logger.debug(f"Cannot determine parent flow index from '{states.flow_index}'")
        return
    
    filter_key = f"__filter__{parent_flow_index}"
    
    # Accumulate filters (for nested @if conditions - AND semantics)
    existing_filters = states.workspace.get(filter_key, [])
    existing_filters.append({
        'truth_mask': truth_mask_data,
        'condition': condition,
        'source_flow_index': states.flow_index,
    })
    states.workspace[filter_key] = existing_filters
    
    logger.info(f"Injected filter for parent '{parent_flow_index}' from condition '{condition}' "
                f"(filter_axis='{truth_mask_data.get('filter_axis')}', total filters: {len(existing_filters)})")


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
        logger.debug(f"Processing '@if' timing marker for condition: {condition}")
        is_ready, to_be_skipped = timer.check_if_condition(condition)
        logger.debug(f"is_ready: {is_ready}, to_be_skipped: {to_be_skipped}")
        if is_ready:
            states.timing_ready = True
            if to_be_skipped:
                states.to_be_skipped = True
            else:
                # Condition passed - inject filter if truth mask is available
                _inject_filter_for_parent(states, timer, condition)

    elif marker == "if!":
        logger.debug(f"Processing '@if!' timing marker for condition: {condition}")
        is_ready, to_be_skipped = timer.check_if_not_condition(condition)
        logger.debug(f"is_ready: {is_ready}, to_be_skipped: {to_be_skipped}")
        if is_ready:
            states.timing_ready = True
            if to_be_skipped:
                states.to_be_skipped = True
            else:
                # Condition passed (inverted) - inject filter if truth mask is available
                # Note: For @if!, we still inject the original truth mask; the inversion
                # was already applied by check_if_not_condition for the skip decision.
                # The truth mask itself represents "elements that matched the condition"
                _inject_filter_for_parent(states, timer, condition)

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