import uuid
import logging
import os
import sys
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Infra Imports ---
try:
    from infra import Inference, Concept, AgentFrame, Reference, BaseStates
    from infra._orchest._blackboard import Blackboard
    from infra._loggers.utils import setup_orchestrator_logging
    from infra._agent._body import Body
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))
    from infra import Inference, Concept, AgentFrame, Reference, BaseStates
    from infra._orchest._blackboard import Blackboard
    from infra._loggers.utils import setup_orchestrator_logging
    from infra._agent._body import Body

# --- Data Classes ---
@dataclass
class ConceptEntry:
    id: str
    concept_name: str
    type: str
    description: Optional[str] = None
    is_ground_concept: bool = False
    is_final_concept: bool = False
    concept: Optional[Concept] = field(default=None, repr=False)

@dataclass
class InferenceEntry:
    id: str
    inference_sequence: str
    concept_to_infer: ConceptEntry
    flow_info: Dict[str, any]
    function_concept: Optional[ConceptEntry] = None
    value_concepts: List[ConceptEntry] = field(default_factory=list)
    context_concepts: List[ConceptEntry] = field(default_factory=list)
    start_without_value: bool = False
    start_without_value_only_once: bool = False
    start_without_function: bool = False
    start_without_function_only_once: bool = False
    inference: Optional[Inference] = field(default=None, repr=False)
    working_interpretation: Optional[Dict[str, any]] = field(default=None, repr=False)

@dataclass
class WaitlistItem:
    """Represents an inference waiting to be processed."""
    inference_entry: InferenceEntry

    def __hash__(self):
        return hash(self.inference_entry.id)

    def __eq__(self, other):
        return isinstance(other, WaitlistItem) and self.inference_entry.id == other.inference_entry.id

@dataclass
class Waitlist:
    """Represents the entire collection of items to be orchestrated."""
    id: str
    items: List[WaitlistItem]
    status: str = "pending"
    
    def sort_by_flow_index(self):
        """Sorts items according to the dot system (flow_index)."""
        def sort_key(item):
            flow_index = item.inference_entry.flow_info['flow_index']
            # Convert dot notation to tuple of integers for proper sorting
            # e.g., '1.2' -> (1, 2), '1.3' -> (1, 3), '1' -> (1,)
            return tuple(int(part) for part in flow_index.split('.'))
        
        self.items.sort(key=sort_key)
        logging.info(f"Waitlist items sorted by flow_index: {[item.inference_entry.flow_info['flow_index'] for item in self.items]}")

    def get_supporting_items(self, target_item: WaitlistItem) -> List[WaitlistItem]:
        """
        Retrieves a list of items that are supporting a specific item.
        An item is considered a "supporter" if its flow_index is a descendant
        of the target item's flow_index (e.g., '1.1' supports '1').
        """
        target_flow_index = target_item.inference_entry.flow_info['flow_index']
        return [
            item for item in self.items
            if item != target_item and item.inference_entry.flow_info['flow_index'].startswith(target_flow_index + '.')
        ]

@dataclass
class ProcessTracker:
    """Tracks the orchestration process and provides statistics."""
    execution_history: List[Dict] = field(default_factory=list)
    completion_order: List[str] = field(default_factory=list)
    cycle_count: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    retry_count: int = 0
    
    def add_execution_record(self, cycle: int, flow_index: str, inference_type: str, 
                           status: str, concept_inferred: str):
        """Adds a record of an execution attempt."""
        record = {
            'cycle': cycle,
            'flow_index': flow_index,
            'inference_type': inference_type,
            'status': status,
            'concept_inferred': concept_inferred
        }
        self.execution_history.append(record)
    
    def record_completion(self, flow_index: str):
        """Records a successful completion."""
        self.completion_order.append(flow_index)
    
    def get_success_rate(self) -> float:
        """Calculates the success rate as a percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100
    
    def log_summary(self, waitlist_id: str, waitlist_items: List['WaitlistItem'], blackboard, concept_repo: 'ConceptRepo'):
        """Logs a comprehensive summary of the orchestration process."""
        logging.info(f"=== Orchestration Summary (ID: {waitlist_id}) ===")
        
        sorted_items = sorted(waitlist_items, key=lambda i: [int(p) for p in i.inference_entry.flow_info['flow_index'].split('.')])
        logging.info("--- Item Status ---")
        for item in sorted_items:
            fi = item.inference_entry.flow_info['flow_index']
            it = item.inference_entry.inference_sequence
            status = blackboard.get_item_status(fi)
            logging.info(f"  - Item {fi:<10} ({it:<12}): {status}")
        
        logging.info("--- Process Statistics ---")
        logging.info(f"  - Total cycles: {self.cycle_count}")
        logging.info(f"  - Total executions: {self.total_executions}")
        logging.info(f"  - Successful completions: {self.successful_executions}")
        logging.info(f"  - Retry attempts: {self.retry_count}")
        logging.info(f"  - Success rate: {self.get_success_rate():.1f}%")
        
        logging.info("--- Completion Order ---")
        for i, flow_index in enumerate(self.completion_order, 1):
            logging.info(f"  {i:2d}. {flow_index}")
        
        logging.info("--- Execution Flow ---")
        for record in self.execution_history:
            status_symbol = "[OK]" if record['status'] == 'completed' else "[RETRY]"
            logging.info(f"  Cycle {record['cycle']}: {status_symbol} {record['flow_index']} ({record['inference_type']}) -> {record['concept_inferred']}")

        logging.info("--- Final Concepts ---")
        for concept_entry in concept_repo.get_all_concepts():
            if concept_entry.is_final_concept:
                ref_tensor = concept_entry.concept.reference.tensor if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - {concept_entry.concept_name}: {ref_tensor}")
                ref_axis_names = concept_entry.concept.reference.axes if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - {concept_entry.concept_name}: {ref_axis_names}")
                ref_shape = concept_entry.concept.reference.shape if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - {concept_entry.concept_name}: {ref_shape}")



# --- Repositories (Data Access) ---

class ConceptRepo:
    def __init__(self, concepts: List[ConceptEntry]):
        self._concept_map = {c.concept_name: c for c in concepts}
        for entry in concepts:
            entry.concept = Concept(entry.concept_name)
            
    def add_reference(self, concept_name: str, data: Any, axis_names: Optional[List[str]] = None):
        """Adds a Reference object to a concept."""
        concept_entry = self.get_concept(concept_name)
        if concept_entry and concept_entry.concept:
            # from_data expects a list.
            if not isinstance(data, list):
                data = [data]
            concept_entry.concept.reference = Reference.from_data(data, axis_names=axis_names)
            logging.info(f"Added reference to concept '{concept_name}'.")
        else:
            logging.warning(f"Could not find concept '{concept_name}' to add reference.")

    def get_concept(self, name: str) -> Optional[ConceptEntry]:
        return self._concept_map.get(name)

    def get_all_concepts(self) -> List[ConceptEntry]:
        return list(self._concept_map.values())

class InferenceRepo:
    def __init__(self, inferences: List[InferenceEntry]):
        self.inferences = inferences
        self._map_by_flow = {inf.flow_info['flow_index']: inf for inf in inferences}
        
        # Initialize Inference objects for each entry
        for entry in inferences:
            if entry.inference is None:
                entry.inference = Inference(
                    entry.inference_sequence,
                    entry.concept_to_infer.concept,
                    entry.function_concept.concept if entry.function_concept else None,
                    [vc.concept for vc in entry.value_concepts],
                    context_concepts=[cc.concept for cc in entry.context_concepts]
                )
    
    def get_all_inferences(self) -> List[InferenceEntry]:
        return self.inferences
    
    def get_inference_by_flow_index(self, idx: str) -> Optional[InferenceEntry]:
        return self._map_by_flow.get(idx)

# --- Orchestrator ---

class Orchestrator:
    """
    Orchestrates a waitlist of inferences, processing them in a bottom-up fashion
    based on the completion of their "support" dependencies.
    """
    def __init__(self, 
                 concept_repo: ConceptRepo,
                 inference_repo: InferenceRepo, 
                 blackboard: Optional[Blackboard] = None,
                 agent_frame_model: str = "demo",
                 body: Optional[Body] = None,
                 max_cycles: int = 10):
        self.inference_repo = inference_repo
        self.concept_repo = concept_repo
        self.agent_frame_model = agent_frame_model
        self.body = body or Body()
        self.waitlist: Optional[Waitlist] = None
        self.blackboard = blackboard or Blackboard()
        self.tracker = ProcessTracker()
        self.max_cycles = max_cycles
        self.workspace = {}
        self._create_waitlist()
        self._initialize_blackboard()

        self._item_by_inferred_concept: Dict[str, WaitlistItem] = {
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

    def _is_function_concept_ready(self, item: WaitlistItem) -> bool:
        """Checks if the function concept for an item is ready."""
        fc = item.inference_entry.function_concept
        return (fc is None) or (self.blackboard.get_concept_status(fc.concept_name) == 'complete')

    def _are_value_concepts_ready(self, item: WaitlistItem) -> bool:
        """Checks if all value concepts for an item are ready."""
        return all(self.blackboard.get_concept_status(vc.concept_name) == 'complete' for vc in item.inference_entry.value_concepts)

    def _is_ready(self, item: WaitlistItem) -> bool:
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

    def _handle_inference_failure(self, item: WaitlistItem, error: Exception):
        """Handles the failed execution of an inference."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.error(f"An error occurred during inference for item {flow_index}: {error}")
        import traceback
        traceback.print_exc()
        self.blackboard.set_item_result(flow_index, f"Error: {error}")

    def _inference_execution(self, item: WaitlistItem) -> str:
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

    def _execute_agent_frame(self, item: WaitlistItem, inference: Inference) -> BaseStates:
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

    def _process_inference_state(self, states: BaseStates, item: WaitlistItem) -> str:
        """
        Processes the state from an inference execution and determines the item's final status.
        """
        self._update_orchestrator_state(states)

        if item.inference_entry.inference_sequence == 'timing':
            return self._handle_timing_inference(states, item)
        
        return self._handle_regular_inference(states, item)

    def _update_orchestrator_state(self, states: BaseStates):
        """Updates the orchestrator's core components from the inference state."""
        if hasattr(states, 'workspace'):
            self.workspace = states.workspace
        if hasattr(states, 'blackboard'):
            self.blackboard = states.blackboard

    def _handle_timing_inference(self, states: BaseStates, item: WaitlistItem) -> str:
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

    def _handle_regular_inference(self, states: BaseStates, item: WaitlistItem) -> str:
        """Handles the logic for all non-timing inferences."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"  -> Inference executed successfully for item {flow_index}")
        self.blackboard.set_item_result(flow_index, "Success")
        
        all_conditions_met = self._update_references_and_check_completion(states, item)
        
        return "completed" if all_conditions_met else "pending"

    def _update_references_and_check_completion(self, states: BaseStates, item: WaitlistItem) -> bool:
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

    def _check_quantifying_completion(self, states: BaseStates, item: WaitlistItem) -> tuple[bool, bool]:
        """Checks if an item is a quantifying inference and whether it has completed."""
        is_quantifying = item.inference_entry.inference_sequence == 'quantifying'
        if not is_quantifying:
            return False, True
        is_complete = getattr(getattr(states, 'syntax', None), 'completion_status', False)
        return True, is_complete

    def _reset_supporting_items(self, item: WaitlistItem):
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

    def _update_concept_from_record(self, record: Any, category: str, item: WaitlistItem):
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

    def _get_concept_name_from_record(self, record: Any, category: str, item: WaitlistItem) -> Optional[str]:
        """Extracts the concept name from a state record."""
        if record.concept:
            return record.concept.name
        if category == 'inference':
            return item.inference_entry.concept_to_infer.concept_name
        return None

    def _update_execution_tracking(self, item: WaitlistItem, status: str):
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

    def _execute_item(self, item: WaitlistItem) -> str:
        """Executes a single waitlist item and updates its status and tracking info."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"Item {flow_index} is ready. Executing.")

        self.blackboard.set_item_status(flow_index, 'in_progress')
        new_status = self._inference_execution(item)

        self.tracker.total_executions += 1
        self.blackboard.set_item_status(flow_index, new_status)

        self._update_execution_tracking(item, new_status)

        return new_status

    def _run_cycle(self, retries_from_previous_cycle: List[WaitlistItem]) -> tuple[bool, List[WaitlistItem]]:
        """Processes one cycle of the orchestration loop."""
        cycle_executions = 0
        cycle_successes = 0
        next_cycle_retries: List[WaitlistItem] = []

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

    def run(self) -> List[ConceptEntry]:
        """Runs the orchestration loop until completion or deadlock."""
        if not self.waitlist:
            logging.error("No waitlist created.")
            return []

        logging.info(f"--- Starting Orchestration for Waitlist {self.waitlist.id} ---")

        retries: List[WaitlistItem] = []

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

# --- Data Definitions ---
def create_sequential_repositories():
    """Creates concept and inference repositories for a waitlist scenario with two intermediate data concepts and three functions."""
    # Create concept entries
    concept_entries = [
        # ConceptEntry(id=str(uuid.uuid4()), concept_name='input_data', type='data', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='intermediate_data_1', type='data'),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='intermediate_data_2', type='data'),
        # ConceptEntry(id=str(uuid.uuid4()), concept_name='output_result', type='data', is_final_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='process_function_1', type='function'),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='::({1}<$({number})%_> add 1)', type='::', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='process_function_3', type='function', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='assign_function', type='function', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='timing_after_1_3', type='function', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='quant_function', type='function'),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='items_to_loop*', type='data'),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='items_to_loop', type='data', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='output_result_after_quantifying', type='data', is_final_concept=True),
    ]
    
    # Create concept repository
    concept_repo = ConceptRepo(concept_entries)
    
    # --- Add initial references for ground concepts ---
    logging.info("Assigning initial references to ground concepts for experiment.")
    concept_repo.add_reference('::({1}<$({number})%_> add 1)', "::({1}<$({number})%_> add 1)", axis_names=['add_imperative'])
    concept_repo.add_reference('process_function_3', "Adds ten to the input.", axis_names=['description'])
    concept_repo.add_reference('assign_function', "Assigns a source concept's reference to a destination concept.", axis_names=['description'])
    concept_repo.add_reference('timing_after_1_3', "A timing function that runs after another concept is complete.", axis_names=['description'])
    concept_repo.add_reference('items_to_loop', ["%(101)", "%(102)", "%(103)"], axis_names=['items'])
    # --- End of initial references ---
    
    # --- Inference 1.1.2: items_to_loop* -> intermediate_data_1 ---
    inf1_to_infer = concept_repo.get_concept('intermediate_data_1')
    inf1_function = concept_repo.get_concept('process_function_1')
    inf1_values = [concept_repo.get_concept('items_to_loop*')]

    # --- Inference 1.1.2.1: timing_after_1_3 => process_function_1 ---
    inf1_1_2_1_to_infer = concept_repo.get_concept('process_function_1')
    inf1_1_2_1_function = concept_repo.get_concept('timing_after_1_3')

    # --- Inference 1.1.3: items_to_loop* -> intermediate_data_2 ---
    inf2_to_infer = concept_repo.get_concept('intermediate_data_2')
    inf2_function = concept_repo.get_concept('::({1}<$({number})%_> add 1)')
    inf2_values = [concept_repo.get_concept('items_to_loop*')]

    # --- Inference 1.1: intermediate_data_2 -> quant_function (Assigning) ---
    inf3_to_infer = concept_repo.get_concept('quant_function')
    inf3_function = concept_repo.get_concept('assign_function')
    inf3_values = [concept_repo.get_concept('intermediate_data_1'), concept_repo.get_concept('intermediate_data_2')]

    # --- Inference 1: items_to_loop -> output_result_after_quantifying ---
    inf4_to_infer = concept_repo.get_concept('output_result_after_quantifying')
    inf4_function = concept_repo.get_concept('quant_function')
    inf4_values = [concept_repo.get_concept('items_to_loop')]
    inf4_context = [concept_repo.get_concept('items_to_loop*'), concept_repo.get_concept('intermediate_data_1')]


    inference_entries = [
        # Quantifying Inference (Controller)
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=inf4_to_infer,
            function_concept=inf4_function,
            value_concepts=inf4_values,
            context_concepts=inf4_context,
            flow_info={'flow_index': '1'},
            working_interpretation={
                "syntax": {
                    "marker": None, 
                    "LoopBaseConcept": "items_to_loop",
                    "ConceptToInfer": ["output_result_after_quantifying"],
                    # "InLoopConcept": {
                    #     "intermediate_data_1": 1
                    # },
                    "completion_status": False,
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True
        ),
        # --- Inferences inside the loop ---
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='assigning',
            concept_to_infer=inf3_to_infer,
            function_concept=inf3_function,
            value_concepts=inf3_values,
            flow_info={'flow_index': '1.1'},
            working_interpretation={
                "syntax": {
                    "marker": ".",
                    "assign_source": "intermediate_data_2",
                    "assign_destination": "quant_function"
                }
            },
        ),
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='simple',
            concept_to_infer=inf1_to_infer,
            function_concept=inf1_function,
            value_concepts=inf1_values,
            flow_info={'flow_index': '1.1.2'},
            working_interpretation={},
        ),
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='imperative',
            concept_to_infer=inf2_to_infer,
            function_concept=inf2_function,
            value_concepts=inf2_values,
            flow_info={'flow_index': '1.1.3'},
            working_interpretation={},
        ),
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='timing',
            concept_to_infer=inf1_1_2_1_to_infer,
            function_concept=inf1_1_2_1_function,
            flow_info={'flow_index': '1.1.2.1'},
            working_interpretation={
                'syntax': {
                    'marker': 'after',
                    'condition': 'intermediate_data_2'
                }
            },
        ),
    ]
    
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo             

if __name__ == "__main__":
    # Setup file logging with timestamp in logs directory
    log_filename = setup_orchestrator_logging(__file__)
    
    # --- Main Execution Logic ---
    logging.info("=== Starting Orchestrator Demo ===")
    
    # 1. Create repositories 
    concept_repo, inference_repo = create_sequential_repositories()

    # 2. Initialize and run the orchestrator with optional Blackboard and AgentFrameModel
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo, 
        # blackboard=Blackboard(),
        # agent_frame_model="demo",
        # body=Body("qwen-turbo-latest")
    )

    # 3. Run the orchestrator
    final_concepts = orchestrator.run()
    
    logging.info("--- Final Concepts Returned ---")
    if final_concepts:
        for concept in final_concepts:
            ref_tensor = concept.concept.reference.tensor if concept.concept and concept.concept.reference is not None else "N/A"
            logging.info(f"  - {concept.concept_name}: {ref_tensor}")
    else:
        logging.info("  No final concepts were returned.")

    logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===") 