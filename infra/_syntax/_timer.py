import logging
from typing import Optional
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
        if self.blackboard.get_concept_status(condition) == 'complete':
            detail = self.blackboard.get_completion_detail_for_concept(condition)
            logger.info(f"@if condition '{condition}' is complete with detail: {detail}")
            if detail == 'condition_not_met':
                return True, True  # Ready, and should be skipped
            elif detail in ['success', None]:
                return True, False  # Ready, not skipped
        
        logger.info(f"@if condition '{condition}' is not complete yet.")
        return False, False  # Not ready 