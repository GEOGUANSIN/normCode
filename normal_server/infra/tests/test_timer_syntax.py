"""
Test script for the refactored Timer class from infra._syntax.

This script demonstrates the usage of the Timer class that has been moved
to the _syntax module and shows its minimal timing condition method.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the project root is in the Python path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the refactored Timer and Blackboard
from infra._syntax import Timer
from infra._orchest._blackboard import Blackboard


def test_timer_functionality():
    """Test the Timer class functionality."""
    logger.info("=== Testing Timer Class from _syntax module ===")
    
    # Create a blackboard with some concept statuses
    blackboard = Blackboard()
    blackboard.set_concept_status("data_loaded", "complete")
    blackboard.set_concept_status("validation_complete", "in_progress")
    blackboard.set_concept_status("processing_complete", "pending")
    
    # Create timer instance
    timer = Timer(blackboard)
    
    # Test progress conditions
    logger.info("\n--- Testing progress conditions ---")
    logger.info(f"check_progress_condition('data_loaded'): {timer.check_progress_condition('data_loaded')}")
    logger.info(f"check_progress_condition('validation_complete'): {timer.check_progress_condition('validation_complete')}")
    logger.info(f"check_progress_condition('processing_complete'): {timer.check_progress_condition('processing_complete')}")
    
    logger.info("\n=== Timer Class Test Complete ===")


if __name__ == "__main__":
    test_timer_functionality() 