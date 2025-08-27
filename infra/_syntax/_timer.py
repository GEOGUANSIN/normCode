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