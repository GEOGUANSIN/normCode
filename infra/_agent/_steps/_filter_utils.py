"""
Shared filter injection utilities for IR steps.
Applies truth mask filters injected by timing conditions (@if/@if!).
"""
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from infra._core._inference import Inference
    from infra._states._common_states import BaseStates

from infra._core._reference import Reference, element_action

logger = logging.getLogger(__name__)

# Truth mask markers
TRUE_MARKER = "%{truth value}(true)"
FALSE_MARKER = "%{truth value}(false)"


def _apply_truth_mask_filter(
    reference: Reference, 
    truth_mask_tensor: List[Any],
    filter_axis: str
) -> Reference:
    """Apply a truth mask filter: false elements become skip values."""
    if filter_axis not in reference.axes:
        return reference
    
    truth_mask_ref = Reference.from_data(truth_mask_tensor, axis_names=[filter_axis])
    skip_value = reference.skip_value
    
    def mask_fn(value, mask):
        return value if mask == TRUE_MARKER else skip_value
    
    try:
        return element_action(mask_fn, [reference, truth_mask_ref])
    except Exception as e:
        logger.warning(f"Failed to apply filter: {e}")
        return reference


def apply_injected_filters(inference: "Inference", states: "BaseStates") -> None:
    """
    Apply any injected filters from timing conditions to value concepts.
    
    Call this at the START of any IR step to apply filters before
    copying references to states.
    
    Requirements:
    - states must have 'workspace' and 'flow_index' attributes
    - If not present, this function safely does nothing
    """
    workspace = getattr(states, 'workspace', None)
    flow_index = getattr(states, 'flow_index', None)
    
    if not workspace or not flow_index:
        return
    
    filter_key = f"__filter__{flow_index}"
    filters = workspace.get(filter_key)
    
    if not filters:
        return
    
    logger.info(f"Applying {len(filters)} injected filter(s) for {flow_index}")
    
    for vc in inference.value_concepts or []:
        if not vc.reference:
            continue
        
        for filter_data in filters:
            truth_mask = filter_data.get('truth_mask', {})
            filter_axis = truth_mask.get('filter_axis')
            truth_mask_tensor = truth_mask.get('tensor')
            
            if filter_axis and truth_mask_tensor:
                vc.reference = _apply_truth_mask_filter(
                    vc.reference, truth_mask_tensor, filter_axis
                )
    
    # Cleanup
    del workspace[filter_key]