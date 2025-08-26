
'''
Demo script for exploring timing concepts in the NormCode framework.

This script demonstrates how to implement timing sequences that execute based on progress conditions.
It focuses on @after and @before concepts that monitor and respond to progress states.

The purpose of the timing sequence is to handle temporal/timing concepts like this:
- @after(condition): Execute sequence after a specific condition/progress has been achieved
- @before(condition): Execute sequence before a specific condition/progress is about to occur
- Progress tracking: Monitor the state of concepts and their execution progress
- Conditional execution: Only run sequences when certain progress conditions are met
'''

import os
import sys
import logging
from typing import Any, Dict, List, Optional, Callable
from types import SimpleNamespace
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
    from infra._states._common_states import BaseStates, SequenceStepSpecLite
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
    from infra import Inference, Concept, Reference, AgentFrame, Body, register_inference_sequence, log_states_progress, ConceptInfoLite, ReferenceRecordLite
    from infra._states._common_states import BaseStates, SequenceStepSpecLite


# --- Create Timer Class ---

class Timer:
    """Encapsulates the logic for timing operations based on progress conditions."""
    
    def __init__(self):
        self.progress_monitors = {}  # Track progress conditions
        self.execution_history = []  # Track execution history
        
    def check_progress_condition(self, condition: str, current_state: Dict) -> bool:
        """
        Check if a progress condition has been met.
        
        Args:
            condition: The condition to check (e.g., "data_loaded", "processing_complete")
            current_state: Current state dictionary with progress information
            
        Returns:
            bool: True if condition is met, False otherwise
        """
        progress = current_state.get("progress", {})
        return progress.get(condition, False)
    
    def execute_after(self, condition: str, sequence_func: Callable, current_state: Dict) -> Dict:
        """
        Execute a sequence after a condition has been met.
        
        Args:
            condition: The condition that must be met
            sequence_func: Function to execute when condition is met
            current_state: Current state information
            
        Returns:
            Dict: Updated state after execution
        """
        if self.check_progress_condition(condition, current_state):
            logger.info(f"Condition '{condition}' met, executing @after sequence")
            result = sequence_func(current_state)
            self.execution_history.append({
                "type": "after",
                "condition": condition,
                "timestamp": time.time(),
                "result": result
            })
            return result
        else:
            logger.info(f"Condition '{condition}' not yet met, waiting...")
            return current_state
    
    def execute_before(self, condition: str, sequence_func: Callable, current_state: Dict) -> Dict:
        """
        Execute a sequence before a condition is about to occur.
        
        Args:
            condition: The condition that is about to occur
            sequence_func: Function to execute before condition occurs
            current_state: Current state information
            
        Returns:
            Dict: Updated state after execution
        """
        # Check if condition is about to occur (e.g., in next step)
        if self.is_condition_imminent(condition, current_state):
            logger.info(f"Condition '{condition}' imminent, executing @before sequence")
            result = sequence_func(current_state)
            self.execution_history.append({
                "type": "before",
                "condition": condition,
                "timestamp": time.time(),
                "result": result
            })
            return result
        else:
            logger.info(f"Condition '{condition}' not imminent, continuing...")
            return current_state
    
    def is_condition_imminent(self, condition: str, current_state: Dict) -> bool:
        """
        Check if a condition is about to occur in the next step.
        
        Args:
            condition: The condition to check
            current_state: Current state information
            
        Returns:
            bool: True if condition is imminent, False otherwise
        """
        # This is a simplified check - in practice, this would analyze the execution plan
        next_steps = current_state.get("next_steps", [])
        return condition in next_steps
    
    def update_progress(self, condition: str, status: bool):
        """Update the progress status for a condition."""
        self.progress_monitors[condition] = status
        logger.info(f"Progress updated: {condition} = {status}")


# --- Create State Class for timing ---

class TimingStates(BaseStates):
    """State container for the timing sequence."""

    def __init__(self) -> None:
        super().__init__()
        self.sequence_state.sequence = [
            SequenceStepSpecLite(step_name="IWI"),
            SequenceStepSpecLite(step_name="IR"),
            SequenceStepSpecLite(step_name="T"),  # Timing
            SequenceStepSpecLite(step_name="OR"),
            SequenceStepSpecLite(step_name="OWI"),
        ]
        self.syntax: SimpleNamespace = SimpleNamespace(
            marker=None,  # "after" or "before"
            condition=None,
            target_sequence=None,
            progress_state={}
        )


# --- Create Agent Frame for timing ---

class TimingAgentFrame(AgentFrame):
    def __init__(self, name: str, working_interpretation: dict, body: Body):
        super().__init__(AgentFrameModel=name, working_interpretation=working_interpretation, body=body)

    def _sequence_setup(self):
        """Sets up the 'timing' inference sequence."""
        logger.debug("Setting up timing demo sequence")
        
        working_interpretation = self.working_interpretation
        body = self.body

        @register_inference_sequence("timing")
        def timing(inference_instance: Inference):
            """`(IWI-IR-T-OR-OWI)`"""
            logger.info("=====EXECUTING TIMING SEQUENCE=====")
            states = TimingStates()
            logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = inference_instance.IWI(inference=inference_instance, states=states, body=body, working_interpretation=working_interpretation); log_states_progress(states, "IWI", "IWI")
            logger.info("---Step 2: Input References (IR)---"); states = inference_instance.IR(inference=inference_instance, states=states); log_states_progress(states, "IR", "IR")
            logger.info("---Step 3: Timing (T)---"); states = inference_instance.T(states=states); log_states_progress(states, "T", "T")
            logger.info("---Step 4: Output Reference (OR)---"); states = inference_instance.OR(states=states); log_states_progress(states, "OR", "OR")
            logger.info("---Step 5: Output Working Interpretation (OWI)---"); states = inference_instance.OWI(states=states); log_states_progress(states, "OWI", "OWI")
            logger.info("=====TIMING SEQUENCE COMPLETED=====")
            return states

    def configure(self, inference_instance: Inference, inference_sequence: str):
        """Configures the steps for the 'timing' sequence."""
        if inference_sequence != "timing":
            logger.warning(f"TimingAgentFrame only supports the 'timing' sequence, not '{inference_sequence}'.")
            return

        methods = {
            "input_working_interpretation": input_working_interpretation,
            "input_references": input_references,
            "timing": timing,
            "output_reference": output_reference,
            "output_working_interpretation": output_working_interpretation,
        }

        logger.debug("Configuring timing demo steps")
        @inference_instance.register_step("IWI")
        def IWI(**fkwargs): return methods.get("input_working_interpretation", self._null_step)(**fkwargs)

        @inference_instance.register_step("IR")
        def IR(**fkwargs): return methods.get("input_references", self._null_step)(**fkwargs)

        @inference_instance.register_step("T")
        def T(**fkwargs): return methods.get("timing", self._null_step)(**fkwargs)

        @inference_instance.register_step("OR")
        def OR(**fkwargs): return methods.get("output_reference", self._null_step)(**fkwargs)

        @inference_instance.register_step("OWI")
        def OWI(**fkwargs): return methods.get("output_working_interpretation", self._null_step)(**fkwargs)


# --- Create Timing Steps ---

def input_working_interpretation(
    inference: Inference,
    states: TimingStates,
    body: Body,
    working_interpretation: Dict[str, Any] | None = None,
) -> TimingStates:
    """Initialize states with syntax info and placeholder records."""
    if working_interpretation:
        syntax_info = working_interpretation.get("syntax", {})
        states.syntax.marker = syntax_info.get("marker")
        states.syntax.condition = syntax_info.get("condition")
        states.syntax.target_sequence = syntax_info.get("target_sequence")
        states.syntax.progress_state = syntax_info.get("progress_state", {})

    # Seed lists with empty records for each step
    for step in ["T", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logging.debug(f"IWI completed. Timing marker: {states.syntax.marker}")
    return states


def input_references(inference: Inference, states: TimingStates) -> TimingStates:
    """Populate references and concept info into the state from the inference instance."""
    if inference.function_concept:
        states.function.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(
                    id=inference.function_concept.id,
                    name=inference.function_concept.name,
                    type=inference.function_concept.type,
                    context=inference.function_concept.context,
                    axis_name=inference.function_concept.axis_name,
                ),
                reference=inference.function_concept.reference.copy()
                if inference.function_concept.reference
                else None,
            )
        )

    for vc in inference.value_concepts or []:
        states.values.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(
                    id=vc.id, name=vc.name, type=vc.type, context=vc.context, axis_name=vc.axis_name
                ),
                reference=vc.reference.copy() if vc.reference else None,
            )
        )

    states.set_current_step("IR")
    logging.debug(f"IR completed. Loaded {len(states.values)} value concepts.")
    return states


def timing(states: TimingStates) -> TimingStates:
    """Check if timing conditions are met and execute if conditions are satisfied."""
    marker = states.syntax.marker
    condition = states.syntax.condition
    progress_state = states.syntax.progress_state
    target_sequence = states.syntax.target_sequence
    
    timer = Timer()
    
    # Update timer with current progress state
    for condition_name, status in progress_state.items():
        timer.update_progress(condition_name, status)
    
    # Check if conditions are met based on marker type
    if marker == "after":
        condition_met = timer.check_progress_condition(condition, {"progress": progress_state})
        logger.info(f"@after condition '{condition}' met: {condition_met}")
    elif marker == "before":
        condition_imminent = timer.is_condition_imminent(condition, {"next_steps": [condition]})
        logger.info(f"@before condition '{condition}' imminent: {condition_imminent}")
        condition_met = condition_imminent
    else:
        logger.warning(f"Unknown timing marker: {marker}")
        condition_met = False
    
    # Execute target sequence if conditions are met
    if condition_met:
        logger.info(f"Executing target sequence: {target_sequence}")
        execution_result = f"Executed {target_sequence} successfully"
        states.set_reference("inference", "T", Reference.from_data([execution_result]))
    else:
        logger.info("Conditions not met, skipping execution")
        states.set_reference("inference", "T", Reference.from_data(["Skipped - conditions not met"]))
    
    states.set_current_step("T")
    logging.debug(f"T completed. Condition met: {condition_met}")
    return states





def output_reference(states: TimingStates) -> TimingStates:
    """Finalize the output reference."""
    t_ref = states.get_reference("inference", "T")
    if t_ref:
        states.set_reference("inference", "OR", t_ref)
    states.set_current_step("OR")
    logging.debug("OR completed.")
    return states


def output_working_interpretation(states: TimingStates) -> TimingStates:
    """No-op finalization for demo."""
    states.set_current_step("OWI")
    logging.debug("OWI completed.")
    return states


# --- Main Execution ---

def run_timing_demo(marker: str, condition: str, target_sequence: str, progress_state: Dict[str, bool]):
    """Sets up and runs a single timing demonstration."""
    logger.info(f"\n----- Running Timing Demo: @{marker}({condition}) -----")

    # 1. Setup concepts and working interpretation
    timer_concept = Concept("timer")
    timer_concept.reference = Reference.from_data([f"@{marker}({condition})"])

    working_interpretation = {
        "syntax": {
            "marker": marker,
            "condition": condition,
            "target_sequence": target_sequence,
            "progress_state": progress_state
        }
    }

    logger.info(f"Progress state: {progress_state}")
    logger.info(f"Target sequence: {target_sequence}")

    # 2. Setup agent and inference
    body = Body()
    agent_frame = TimingAgentFrame("timing_demo", working_interpretation, body)
    
    inference = Inference(
        sequence_name="timing",
        function_concept=timer_concept,
        value_concepts=[timer_concept]
    )

    # 3. Configure and run the sequence
    agent_frame.configure(inference, "timing")
    result_states = inference.execute()

    # 4. Log the result
    final_reference = result_states.get_reference("inference", "OR")
    if final_reference:
        logger.info(f"Final result: {final_reference.get()}")
    else:
        logger.warning("Sequence did not produce an output reference.")
    logger.info("----- Timing Demo Complete -----")


if __name__ == "__main__":
    # Demo 1: @after - Execute after data is loaded
    run_timing_demo(
        marker="after",
        condition="data_loaded",
        target_sequence="process_data",
        progress_state={"data_loaded": True, "processing_complete": False}
    )

    # Demo 2: @before - Execute before processing starts
    run_timing_demo(
        marker="before",
        condition="processing_start",
        target_sequence="prepare_environment",
        progress_state={"data_loaded": True, "processing_start": False}
    )

    # Demo 3: @after - Condition not met, should skip
    run_timing_demo(
        marker="after",
        condition="validation_complete",
        target_sequence="finalize_results",
        progress_state={"data_loaded": True, "validation_complete": False}
    )