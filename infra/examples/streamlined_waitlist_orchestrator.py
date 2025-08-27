import uuid
import logging
import os
import sys
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

# --- Infra Imports ---
try:
    from infra import Inference, Concept, AgentFrame
    from infra._orchest._blackboard import Blackboard
    from infra._loggers.utils import setup_orchestrator_logging
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))
    from infra import Inference, Concept, AgentFrame
    from infra._orchest._blackboard import Blackboard
    from infra._loggers.utils import setup_orchestrator_logging

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
    function_concept: Optional[ConceptEntry]
    value_concepts: List[ConceptEntry]
    flow_info: Dict[str, any]
    start_without_value: bool = False
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
                ref = concept_entry.concept.reference if concept_entry.concept and concept_entry.concept.reference is not None else "N/A"
                logging.info(f"  - {concept_entry.concept_name}: {ref}")



# --- Repositories (Data Access) ---

class ConceptRepo:
    def __init__(self, concepts: List[ConceptEntry]):
        self._concept_map = {c.concept_name: c for c in concepts}
        for entry in concepts:
            entry.concept = Concept(entry.concept_name)
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
                    [vc.concept for vc in entry.value_concepts]
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
                 agent_frame: AgentFrame = None,
                 max_cycles: int = 10):
        self.inference_repo = inference_repo
        self.concept_repo = concept_repo
        self.agent_frame = agent_frame
        self.waitlist: Optional[Waitlist] = None
        self.blackboard = blackboard or Blackboard()
        self.tracker = ProcessTracker()
        self.max_cycles = max_cycles
        self._create_waitlist()
        self._initialize_blackboard()

        self._item_by_inferred_concept: Dict[str, WaitlistItem] = {
            item.inference_entry.concept_to_infer.concept_name: item for item in self.waitlist.items
        }

    def _create_waitlist(self):
        """Creates the waitlist from the inference repository."""
        items = [WaitlistItem(inference_entry=inf) for inf in self.inference_repo.get_all_inferences()]
        self.waitlist = Waitlist(id=str(uuid.uuid4()), items=items)
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
        An item is ready if its function concept is 'complete' and other readiness conditions are met.
        """
        if not self._is_function_concept_ready(item):
            return False

        if item.inference_entry.start_without_value:
            return True

        return self._are_value_concepts_ready(item)

    def _handle_inference_success(self, item: WaitlistItem):
        """Handles the successful execution of an inference."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"  -> Inference executed successfully for item {flow_index}")
        self.blackboard.set_item_result(flow_index, "Success")
        concept_to_update = item.inference_entry.concept_to_infer
        self.blackboard.set_concept_status(concept_to_update.concept_name, 'complete')
        logging.info(f"  -> Concept '{concept_to_update.concept_name}' set to 'complete'.")

    def _handle_inference_failure(self, item: WaitlistItem, error: Exception):
        """Handles the failed execution of an inference."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.error(f"An error occurred during inference for item {flow_index}: {error}")
        import traceback
        traceback.print_exc()
        self.blackboard.set_item_result(flow_index, f"Error: {error}")

    def _inference_execution(self, item: WaitlistItem) -> str:
        """
        Executes a real inference using the provided AgentFrame.
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
            self.agent_frame.configure(inference, item.inference_entry.inference_sequence)
            inference.execute()
            self._handle_inference_success(item)
            return "completed"

        except Exception as e:
            self._handle_inference_failure(item, e)
            return "failed"

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
def create_simple_repositories():
    """Creates concept and inference repositories for a simple waitlist scenario."""
    # Create concept entries
    concept_entries = [
        ConceptEntry(id=str(uuid.uuid4()), concept_name='input_data', type='data', is_ground_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='output_result', type='data', is_final_concept=True),
        ConceptEntry(id=str(uuid.uuid4()), concept_name='process_function', type='function', is_ground_concept=True),
    ]
    
    # Create concept repository
    concept_repo = ConceptRepo(concept_entries)
    
    # Create inference entries
    concept_to_infer = concept_repo.get_concept('output_result')
    function_concept = concept_repo.get_concept('process_function')
    value_concepts = [concept_repo.get_concept('input_data')]

    inference_entries = [
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='simple',
            concept_to_infer=concept_to_infer,
            function_concept=function_concept,
            value_concepts=value_concepts,
            flow_info={'flow_index': '1'},
            working_interpretation={}
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
    concept_repo, inference_repo = create_simple_repositories()

    # 2. Initialize and run the orchestrator with Blackboard and AgentFrame
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo, 
        blackboard=Blackboard(),
        agent_frame=AgentFrame("demo")
    )

    # 3. Run the orchestrator
    final_concepts = orchestrator.run()
    
    logging.info("--- Final Concepts Returned ---")
    if final_concepts:
        for concept in final_concepts:
            ref = concept.concept.reference if concept.concept and concept.concept.reference is not None else "N/A"
            logging.info(f"  - {concept.concept_name}: {ref}")
    else:
        logging.info("  No final concepts were returned.")

    logging.info(f"=== Orchestrator Demo Complete - Log saved to {log_filename} ===") 