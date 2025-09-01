import uuid
import logging
from typing import List, Optional, Dict, Any

# Import dependencies
from infra import Inference, Concept, AgentFrame, Reference, BaseStates
from infra._orchest._blackboard import Blackboard
from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
from infra._orchest._waitlist import WaitlistItem, Waitlist
from infra._orchest._tracker import ProcessTracker
from infra._agent._body import Body

class Orchestrator:
    """
    Orchestrates a waitlist of inferences, processing them in a bottom-up fashion
    based on the completion of their "support" dependencies.
    """
    def __init__(self, 
                 concept_repo: 'ConceptRepo',
                 inference_repo: 'InferenceRepo', 
                 blackboard: Optional['Blackboard'] = None,
                 agent_frame_model: str = "demo",
                 body: Optional['Body'] = None,
                 max_cycles: int = 30):
        self.inference_repo = inference_repo
        self.concept_repo = concept_repo
        self.agent_frame_model = agent_frame_model
        self.body = body or Body()
        self.waitlist: Optional['Waitlist'] = None
        self.blackboard = blackboard or Blackboard()
        self.tracker = ProcessTracker()
        self.max_cycles = max_cycles
        self.workspace = {}
        self._create_waitlist()
        self._initialize_blackboard()

        self._item_by_inferred_concept: Dict[str, 'WaitlistItem'] = {
            item.inference_entry.concept_to_infer.concept_name: item for item in self.waitlist.items
        }

    def _create_waitlist(self):
        """Creates the waitlist from the inference repository."""
        items = [WaitlistItem(inference_entry=inf) for inf in self.inference_repo.get_all_inferences()]
        self.waitlist = Waitlist(id=str(uuid.uuid4()), items=items)
        self.waitlist.sort_by_flow_index()
        logging.info(f"Created waitlist {self.waitlist.id} with {len(self.waitlist.items)} items.")

    def _initialize_blackboard(self):
        """Initializes all concept and item states in the Blackboard."""
        if not self.waitlist:
            logging.error("Cannot initialize blackboard without a waitlist.")
            return

        all_concepts = list(self.concept_repo._concept_map.values())
        self.blackboard.initialize_states(all_concepts, self.waitlist.items)
        
        logging.info("Blackboard states initialized.")

    def _is_function_concept_ready(self, item: 'WaitlistItem') -> bool:
        """Checks if the function concept for an item is ready."""
        fc = item.inference_entry.function_concept
        return (fc is None) or (self.blackboard.get_concept_status(fc.concept_name) == 'complete')

    def _are_value_concepts_ready(self, item: 'WaitlistItem') -> bool:
        """Checks if all value concepts for an item are ready."""
        return all(self.blackboard.get_concept_status(vc.concept_name) == 'complete' for vc in item.inference_entry.value_concepts)

    def _is_ready(self, item: 'WaitlistItem') -> bool:
        """
        An item is ready if its dependencies are met. Certain flags can bypass checks.
        """
        flow_index = item.inference_entry.flow_info['flow_index']
        is_first_execution = self.blackboard.get_execution_count(flow_index) == 0

        # Check function concept readiness, unless bypassed
        if not item.inference_entry.start_without_function:
            if not (item.inference_entry.start_without_function_only_once and is_first_execution):
                if not self._is_function_concept_ready(item):
                    return False

        # Check value concept readiness, unless bypassed
        if item.inference_entry.start_without_value:
            return True

        if item.inference_entry.start_without_value_only_once and is_first_execution:
            return True

        return self._are_value_concepts_ready(item)

    def _handle_inference_failure(self, item: 'WaitlistItem', error: Exception):
        """Handles the failed execution of an inference."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.error(f"An error occurred during inference for item {flow_index}: {error}")
        import traceback
        traceback.print_exc()
        self.blackboard.set_item_result(flow_index, f"Error: {error}")

    def _inference_execution(self, item: 'WaitlistItem') -> str:
        """
        Executes a real inference using a fresh AgentFrame for each execution.
        Updates the item's result and returns the new status.
        """
        flow_index = item.inference_entry.flow_info['flow_index']
        self.blackboard.increment_execution_count(flow_index)

        inference = item.inference_entry.inference
        if not inference:
            logging.error(f"Item {flow_index} has no Inference object to execute.")
            self.blackboard.set_item_result(flow_index, "Error: Missing Inference object")
            return "failed"

        try:
            states = self._execute_agent_frame(item, inference)
            return self._process_inference_state(states, item)

        except Exception as e:
            self._handle_inference_failure(item, e)
            return "failed"

    def _execute_agent_frame(self, item: 'WaitlistItem', inference: 'Inference') -> 'BaseStates':
        """Creates and executes an AgentFrame for a given inference."""
        working_interpretation = item.inference_entry.working_interpretation or {}
        working_interpretation["blackboard"] = self.blackboard
        working_interpretation["workspace"] = self.workspace
        
        agent_frame = AgentFrame(
            self.agent_frame_model,
            working_interpretation=working_interpretation,
            body=self.body
        )
        agent_frame.configure(inference, item.inference_entry.inference_sequence)
        return inference.execute()

    def _process_inference_state(self, states: 'BaseStates', item: 'WaitlistItem') -> str:
        """
        Processes the state from an inference execution and determines the item's final status.
        """
        self._update_orchestrator_state(states)

        if item.inference_entry.inference_sequence == 'timing':
            return self._handle_timing_inference(states, item)
        
        return self._handle_regular_inference(states, item)

    def _update_orchestrator_state(self, states: 'BaseStates'):
        """Updates the orchestrator's core components from the inference state."""
        if hasattr(states, 'workspace'):
            self.workspace = states.workspace
        if hasattr(states, 'blackboard'):
            self.blackboard = states.blackboard

    def _handle_timing_inference(self, states: 'BaseStates', item: 'WaitlistItem') -> str:
        """Handles the specific logic for timing inferences."""
        flow_index = item.inference_entry.flow_info['flow_index']
        timing_ready = getattr(states, 'timing_ready', True)

        if not timing_ready:
            logging.info(f"Timing condition for item {flow_index} not met. Item will be retried.")
            return "pending"
        
        logging.info(f"Timing condition for item {flow_index} met. Item will be completed.")
        self.blackboard.set_item_result(flow_index, "Success")
        concept_name = item.inference_entry.concept_to_infer.concept_name
        self.blackboard.set_concept_status(concept_name, 'complete')
        return "completed"

    def _handle_regular_inference(self, states: 'BaseStates', item: 'WaitlistItem') -> str:
        """Handles the logic for all non-timing inferences."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"  -> Inference executed successfully for item {flow_index}")
        self.blackboard.set_item_result(flow_index, "Success")
        
        all_conditions_met = self._update_references_and_check_completion(states, item)
        
        return "completed" if all_conditions_met else "pending"

    def _update_references_and_check_completion(self, states: 'BaseStates', item: 'WaitlistItem') -> bool:
        """
        For quantifying loops, resets supporting items first, then updates all concept references from the state.
        This "reset first, then update" approach ensures the system is correctly prepared for the next loop iteration.
        Returns True if all conditions are met, False otherwise.
        """
        # 1. Check if the quantifying loop has completed.
        is_quantifying, is_complete = self._check_quantifying_completion(states, item)

        # 2. If the loop is not complete, reset the supporting items first.
        if is_quantifying and not is_complete:
            self._reset_supporting_items(item)

        # 3. Always update all concept references with the results from the latest inference.
        # This populates the blackboard with the necessary inputs for the *next* loop iteration.
        for category in ['inference', 'context']:
            if hasattr(states, category):
                for record in getattr(states, category):
                    if record.step_name == 'OR' and record.reference is not None:
                        self._update_concept_from_record(record, category, item)

        # 4. The overall process is only "complete" if the quantifying loop is finished.
        return not (is_quantifying and not is_complete)

    def _check_quantifying_completion(self, states: 'BaseStates', item: 'WaitlistItem') -> tuple[bool, bool]:
        """Checks if an item is a quantifying inference and whether it has completed."""
        is_quantifying = item.inference_entry.inference_sequence == 'quantifying'
        if not is_quantifying:
            return False, True
        is_complete = getattr(getattr(states, 'syntax', None), 'completion_status', False)
        return True, is_complete

    def _reset_supporting_items(self, item: 'WaitlistItem'):
        """Resets the status of all items that support the given item."""
        supporting_items = self.waitlist.get_supporting_items(item)
        if not supporting_items:
            return
            
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"Quantifying loop for item {flow_index} not complete. Resetting supporters.")
        
        for support_item in supporting_items:
            support_flow_index = support_item.inference_entry.flow_info['flow_index']
            self.blackboard.set_item_status(support_flow_index, 'pending')

            inferred_concept_entry = support_item.inference_entry.concept_to_infer
            if not inferred_concept_entry.is_ground_concept:
                self.blackboard.set_concept_status(inferred_concept_entry.concept_name, 'pending')
                if inferred_concept_entry.concept:
                    inferred_concept_entry.concept.reference = None
                logging.info(f"  - Reset item {support_flow_index} and concept '{inferred_concept_entry.concept_name}' to pending.")

    def _update_concept_from_record(self, record: Any, category: str, item: 'WaitlistItem'):
        """Processes a single 'OR' record from the inference state, updating the concept reference."""
        concept_name = self._get_concept_name_from_record(record, category, item)
        if not concept_name:
            return

        concept_entry = self.concept_repo.get_concept(concept_name)
        if not (concept_entry and concept_entry.concept):
            logging.warning(f"Could not find concept '{concept_name}' in repo to update reference.")
            return

        concept_entry.concept.reference = record.reference.copy()
        logging.info(f"Updated reference for concept '{concept_name}' from inference state.")

        self.blackboard.set_concept_status(concept_name, 'complete')
        logging.info(f"Concept '{concept_name}' set to 'complete' on blackboard after reference update.")

    def _get_concept_name_from_record(self, record: Any, category: str, item: 'WaitlistItem') -> Optional[str]:
        """Extracts the concept name from a state record."""
        if record.concept:
            return record.concept.name
        if category == 'inference':
            return item.inference_entry.concept_to_infer.concept_name
        return None

    def _update_execution_tracking(self, item: 'WaitlistItem', status: str):
        """Updates the process tracker after an item execution attempt."""
        flow_index = item.inference_entry.flow_info['flow_index']

        self.tracker.add_execution_record(
            cycle=self.tracker.cycle_count,
            flow_index=flow_index,
            inference_type=item.inference_entry.inference_sequence,
            status=status,
            concept_inferred=item.inference_entry.concept_to_infer.concept_name
        )

        if status == 'completed':
            logging.info(f"Item {flow_index} COMPLETED.")
            self.tracker.successful_executions += 1
            self.tracker.record_completion(flow_index)
        else:
            logging.info(f"Item {flow_index} did not complete, will retry.")
            self.tracker.retry_count += 1

    def _execute_item(self, item: 'WaitlistItem') -> str:
        """Executes a single waitlist item and updates its status and tracking info."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"Item {flow_index} is ready. Executing.")

        self.blackboard.set_item_status(flow_index, 'in_progress')
        new_status = self._inference_execution(item)

        self.tracker.total_executions += 1
        self.blackboard.set_item_status(flow_index, new_status)

        self._update_execution_tracking(item, new_status)

        return new_status

    def _run_cycle(self, retries_from_previous_cycle: List['WaitlistItem']) -> tuple[bool, List['WaitlistItem']]:
        """Processes one cycle of the orchestration loop."""
        cycle_executions = 0
        cycle_successes = 0
        next_cycle_retries: List['WaitlistItem'] = []

        # Get items to process for this cycle, prioritizing retries
        retried_items_set = set(retries_from_previous_cycle)
        items_to_process = retries_from_previous_cycle + [
            item for item in self.waitlist.items if item not in retried_items_set
        ]

        for item in items_to_process:
            flow_index = item.inference_entry.flow_info['flow_index']
            if self.blackboard.get_item_status(flow_index) == 'pending' and self._is_ready(item):
                cycle_executions += 1
                new_status = self._execute_item(item)

                if new_status == 'completed':
                    cycle_successes += 1
                else:
                    next_cycle_retries.append(item)

        logging.info(f"Cycle {self.tracker.cycle_count}: {cycle_executions} executions, {cycle_successes} completions")

        return cycle_executions > 0, next_cycle_retries

    def _log_stuck_items(self):
        """Logs items that are not completed when a deadlock is detected."""
        stuck_items = [i.inference_entry.flow_info['flow_index'] for i in self.waitlist.items if self.blackboard.get_item_status(i.inference_entry.flow_info['flow_index']) != 'completed']
        logging.warning(f"Stuck items: {stuck_items}")

    def run(self) -> List['ConceptEntry']:
        """Runs the orchestration loop until completion or deadlock."""
        if not self.waitlist:
            logging.error("No waitlist created.")
            return []

        logging.info(f"--- Starting Orchestration for Waitlist {self.waitlist.id} ---")

        retries: List['WaitlistItem'] = []

        while self.blackboard.get_all_pending_or_in_progress_items() and self.tracker.cycle_count < self.max_cycles:
            self.tracker.cycle_count += 1
            logging.info(f"--- Cycle {self.tracker.cycle_count} ---")
            
            progress_made, retries = self._run_cycle(retries)
            
            if not progress_made:
                logging.warning("No progress made in the last cycle. Deadlock detected.")
                self._log_stuck_items()
                break
        
        if self.tracker.cycle_count >= self.max_cycles:
            logging.error(f"Maximum cycles ({self.max_cycles}) reached. Stopping orchestration.")
        
        logging.info(f"--- Orchestration Finished for Waitlist {self.waitlist.id} ---")
        
        # Automatically log summary when orchestration completes
        if self.waitlist:
            self.tracker.log_summary(self.waitlist.id, self.waitlist.items, self.blackboard, self.concept_repo)

        final_concepts = [c for c in self.concept_repo.get_all_concepts() if c.is_final_concept]
        return final_concepts
