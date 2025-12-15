import logging
from typing import Optional, Dict, Any
from infra._orchest._blackboard import Blackboard

logger = logging.getLogger(__name__)


class Timer:
    """Encapsulates logic for timing operations based on a Blackboard."""
    
    def __init__(self, blackboard: Optional[Blackboard] = None):
        self.blackboard = blackboard

    def check_progress_condition(self, condition: str) -> bool:
        """Checks if a condition is met by querying the blackboard."""
        return self.blackboard.check_progress_condition(condition)

    def check_if_condition(self, condition: str) -> tuple[bool, bool]:
        """
        Checks an 'if' condition, returning readiness and whether to skip.
        Returns:
            A tuple (is_ready, to_be_skipped).
        """
        concept_status = self.blackboard.get_concept_status(condition)
        logger.debug(f"Checking @if condition '{condition}'. Status: {concept_status}")
        if concept_status == 'complete':
            detail = self.blackboard.get_completion_detail_for_concept(condition)
            logger.info(f"@if condition '{condition}' is complete with detail: {detail}")
            if detail == 'condition_not_met':
                logger.debug(f"@if condition '{condition}' not met, returning ready and skip.")
                return True, True  # Ready, and should be skipped
            elif detail in ['success', None]:
                logger.debug(f"@if condition '{condition}' met, returning ready and no skip.")
                return True, False  # Ready, not skipped
        
        logger.info(f"@if condition '{condition}' is not complete yet.")
        return False, False  # Not ready

    def check_if_not_condition(self, condition: str) -> tuple[bool, bool]:
        """
        Checks an 'if!' condition, returning readiness and whether to skip.
        This is the reverse of the 'if' condition.
        Returns:
            A tuple (is_ready, to_be_skipped).
        """
        concept_status = self.blackboard.get_concept_status(condition)
        logger.debug(f"Checking @if! condition '{condition}'. Status: {concept_status}")
        if self.blackboard.get_concept_status(condition) == 'complete':
            detail = self.blackboard.get_completion_detail_for_concept(condition)
            logger.info(f"@if! condition '{condition}' is complete with detail: {detail}")
            if detail == 'condition_not_met':
                logger.debug(f"@if! condition '{condition}' not met, returning ready and no skip.")
                return True, False  # Ready, not skipped
            elif detail in ['success', None]:
                logger.debug(f"@if! condition '{condition}' met, returning ready and skip.")
                return True, True  # Ready, and should be skipped
        
        logger.info(f"@if! condition '{condition}' is not complete yet.")
        return False, False  # Not ready

    def get_truth_mask_for_filter(self, condition: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the truth mask for a judgement condition to enable filter injection.
        
        This is used when a timing condition (@if/@if!) passes and we want to
        inject a filter for the parent inference's IR step to apply.
        
        Args:
            condition: The judgement concept name (e.g., '<doc is relevant>')
            
        Returns:
            Truth mask data dict containing:
            - 'tensor': The truth mask data (list of '%{truth value}(true/false)')
            - 'axes': List of axis names
            - 'filter_axis': The primary filter axis name
            Or None if no truth mask is available for this condition.
        """
        if not self.blackboard:
            logger.warning("No blackboard available for truth mask lookup")
            return None
            
        truth_mask = self.blackboard.get_truth_mask(condition)
        if truth_mask:
            logger.debug(f"Retrieved truth mask for '{condition}' with filter_axis='{truth_mask.get('filter_axis')}'")
        else:
            logger.debug(f"No truth mask found for '{condition}'")
        return truth_mask