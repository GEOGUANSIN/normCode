
'''
Demo script for exploring timing concepts in the NormCode framework.

This script demonstrates how to implement timing sequences that execute based on progress conditions.
It focuses on @after concepts that monitor and respond to progress states.

The purpose of the timing sequence is to handle temporal/timing concepts like this:
- @after(condition): Execute sequence after a specific condition/progress has been achieved
- Progress tracking: Monitor the state of concepts and their execution progress
- Conditional execution: Only run sequences when certain progress conditions are met
'''

import os
import sys
import logging
from typing import Any, Dict, List, Optional, Callable
import time
import threading

# Configure logging to show INFO messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the project root is in the Python path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import core components
try:
    from infra import Inference, Concept, Reference, AgentFrame, Body, register_inference_sequence, log_states_progress, ConceptInfoLite, ReferenceRecordLite
    from infra._states import TimingStates
    from infra._orchest._blackboard import Blackboard
    from infra._syntax import Timer
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
    from infra import Inference, Concept, Reference, AgentFrame, Body, register_inference_sequence, log_states_progress, ConceptInfoLite, ReferenceRecordLite
    from infra._states import TimingStates
    from infra._orchest._blackboard import Blackboard
    from infra._syntax import Timer


# --- Main Execution ---

def run_timing_demo(marker: str, condition: str, progress_state: Dict[str, bool]):
    """Sets up and runs a single timing demonstration."""
    logger.info(f"\n----- Running Timing Demo: @{marker}({condition}) -----")

    # 1. Setup concepts and working interpretation
    timer_concept = Concept("timer")
    # timer_concept.reference = Reference.from_data([f"@{marker}({condition})"])

    # In a real scenario, an orchestrator would build the working_interpretation,
    # including the blackboard, based on its current state of all concepts.
    blackboard = Blackboard()
    for concept_name, is_complete in progress_state.items():
        status = "complete" if is_complete else "pending"
        blackboard.set_concept_status(concept_name, status)

    working_interpretation = {
        "blackboard": blackboard,  # Pass the blackboard object
        "syntax": {
            "marker": marker,
            "condition": condition,
        }
    }

    logger.info(f"Progress state: {progress_state}")

    # 2. Setup agent and inference
    body = Body()
    agent_frame = AgentFrame("demo", working_interpretation, body=body)
    
    # Create a placeholder concept to infer
    placeholder_concept = Concept("timing_check")
    
    inference = Inference(
        sequence_name="timing",
        function_concept=timer_concept,
        concept_to_infer=placeholder_concept
    )

    # 3. Configure and run the sequence
    agent_frame.configure(inference, "timing")
    result_states = inference.execute()

    # 4. Log the result
    logger.info(f"Final result: timing_ready = {result_states.timing_ready}")
    logger.info("----- Timing Demo Complete -----")


if __name__ == "__main__":
    # Demo 1: @after - Execute after data is loaded
    run_timing_demo(
        marker="after",
        condition="data_loaded",
        progress_state={"data_loaded": True, "processing_complete": False}
    )

    # Demo 2: @after - Condition not met, should skip
    run_timing_demo(
        marker="after",
        condition="validation_complete",
        progress_state={"data_loaded": True, "validation_complete": False}
    )