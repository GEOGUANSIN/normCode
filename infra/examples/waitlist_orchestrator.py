import uuid
import logging
import os
import sys
import time
import random
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Infra Imports ---
try:
    from infra import Inference, Concept
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))
    from infra import Inference, Concept

# --- Normal Code Example ---
Normcode_example = """
[all {index} and {digit} of number]
    <= *every({number})%:[{number}]@[{index}^1] |1
        <= $.([{index} and {digit}]*) |1.1
        <- [{index} and {digit}]* 
            <= &in({index}*;{digit}*) |1.1.2
            <- {index}* 
            <- {unit place value}*
                <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>) |1.1.2.3
                <- {unit place digit}?<:{2}>
                <- {number}<$={a}><:{1}>
        <- {number}<$={a}>
            <= $+({new number}:{number}) |1.1.3
                <= @after([{index} and {digit}]*) |1.1.3.1
            <- {new number}
                <= ::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>) |1.1.3.2
                <- {unit place digit}?<:{2}> 
                <- {number}<$={a}><:{1}>
        <- {index}*
            <= ::(increment {1}<$({index})%_> by 1) |1.1.4
                <= @after([{index} and {digit}]*) |1.1.4.1
            <- {index}*
    <- {number}<$={a}>
"""

# --- Data Structures ---

@dataclass
class ConceptEntry:
    id: str
    concept_name: str
    type: str
    description: Optional[str] = None
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

@dataclass
class Blackboard:
    """Manages the dynamic state of all concepts and inference items."""
    concept_statuses: Dict[str, str] = field(default_factory=dict)  # concept_name -> status
    item_statuses: Dict[str, str] = field(default_factory=dict)     # flow_index -> status
    item_results: Dict[str, any] = field(default_factory=dict)      # flow_index -> result
    item_execution_counts: Dict[str, int] = field(default_factory=dict) # flow_index -> count
    completed_concept_timestamps: Dict[str, float] = field(default_factory=dict)  # concept_name -> timestamp

    def initialize_states(self, concepts: List[ConceptEntry], items: List[WaitlistItem]):
        """Sets the initial state for all concepts and items."""
        for concept in concepts:
            self.concept_statuses[concept.concept_name] = "empty"
        for item in items:
            flow_index = item.inference_entry.flow_info['flow_index']
            self.item_statuses[flow_index] = "pending"
            self.item_execution_counts[flow_index] = 0
            self.item_results[flow_index] = None

    def get_concept_status(self, concept_name: str) -> str:
        return self.concept_statuses.get(concept_name, "empty")

    def set_concept_status(self, concept_name: str, status: str):
        self.concept_statuses[concept_name] = status
        if status == 'complete':
            if concept_name not in self.completed_concept_timestamps:
                self.completed_concept_timestamps[concept_name] = time.time()
                logging.info(f"  -> Blackboard: Recorded completion of '{concept_name}'.")

    def get_item_status(self, flow_index: str) -> str:
        return self.item_statuses.get(flow_index, "pending")

    def set_item_status(self, flow_index: str, status: str):
        self.item_statuses[flow_index] = status
    
    def get_item_result(self, flow_index: str) -> any:
        return self.item_results.get(flow_index)

    def set_item_result(self, flow_index: str, result: any):
        self.item_results[flow_index] = result

    def get_execution_count(self, flow_index: str) -> int:
        return self.item_execution_counts.get(flow_index, 0)

    def increment_execution_count(self, flow_index: str):
        self.item_execution_counts[flow_index] = self.get_execution_count(flow_index) + 1

    def get_all_pending_or_in_progress_items(self) -> bool:
        return any(s in ['pending', 'in_progress'] for s in self.item_statuses.values())

    def get_completed_concepts(self) -> List[str]:
        return list(self.completed_concept_timestamps.keys())

# --- Repositories (Data Access) ---

class ConceptRepo:
    def __init__(self, concepts: List[ConceptEntry]):
        self._concept_map = {c.concept_name: c for c in concepts}
        for entry in concepts:
            entry.concept = Concept(entry.concept_name)
    def get_concept(self, name: str) -> Optional[ConceptEntry]:
        return self._concept_map.get(name)

class InferenceRepo:
    def __init__(self, inferences: List[InferenceEntry]):
        self.inferences = inferences
        self._map_by_flow = {inf.flow_info['flow_index']: inf for inf in inferences}
    def get_all_inferences(self) -> List[InferenceEntry]:
        return self.inferences
    def get_inference_by_flow_index(self, idx: str) -> Optional[InferenceEntry]:
        return self._map_by_flow.get(idx)

# --- Data Definitions ---
concept_entries: List[ConceptEntry] = [
    ConceptEntry(id=str(uuid.uuid4()), concept_name="[all {index} and {digit} of number]", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="*every({number})%:[{number}]@[{index}^1]", type="quantifying"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="$.([{index} and {digit}]*)", type="assigning"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="[{index} and {digit}]*", type="grouping"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="&in({index}*;{digit}*)", type="grouping"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="{index}*", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="{unit place value}*", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)", type="imperative"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="{unit place digit}?", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="@after([{index} and {digit}]*)", type="timing"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="$+({new number}:{number})", type="assigning"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="{new number}", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)", type="imperative"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="::(increment {1}<$({index})%_> by 1)", type="imperative"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="{number}", type="object")
]
concept_repo = ConceptRepo(concept_entries)

inference_entries: List[InferenceEntry] = [
    # 1. Quantifying Loop (Root)
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="quantifying", 
                   concept_to_infer=concept_repo.get_concept("[all {index} and {digit} of number]"), 
                   function_concept=concept_repo.get_concept("*every({number})%:[{number}]@[{index}^1]"), 
                   value_concepts=[concept_repo.get_concept("{number}")], 
                   flow_info={"flow_index": "1", "support": ["1.1"]}, start_without_value=True),
    
    # 1.1. Assigning value for the quantifier based on the loop's output
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="assigning", 
                   concept_to_infer=concept_repo.get_concept("*every({number})%:[{number}]@[{index}^1]"), 
                   function_concept=concept_repo.get_concept("$.([{index} and {digit}]*)"), 
                   value_concepts=[concept_repo.get_concept("[{index} and {digit}]*"), concept_repo.get_concept("{number}"), concept_repo.get_concept("{index}*")], 
                   flow_info={"flow_index": "1.1", "support": ["1.1.2", "1.1.3", "1.1.4"], "target": ["1"]}),
    
    # 1.1.2. Grouping index and digit, which is the main output of the loop body
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="grouping", 
                   concept_to_infer=concept_repo.get_concept("[{index} and {digit}]*"), 
                   function_concept=concept_repo.get_concept("&in({index}*;{digit}*)"), 
                   value_concepts=[concept_repo.get_concept("{index}*"), concept_repo.get_concept("{unit place value}*")], 
                   flow_info={"flow_index": "1.1.2", "support": ["1.1.2.3"], "target": ["1.1"]}),
    
    # 1.1.2.3. Getting the unit place value (digit) - the first step in the loop
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="imperative", 
                   concept_to_infer=concept_repo.get_concept("{unit place value}*"), 
                   function_concept=concept_repo.get_concept("::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)"), 
                   value_concepts=[concept_repo.get_concept("{unit place digit}?"), concept_repo.get_concept("{number}")], 
                   flow_info={"flow_index": "1.1.2.3", "target": ["1.1.2"]}),

    # 1.1.3. Assign the new number back to the main {number} concept for the next loop.
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="assigning", 
                   concept_to_infer=concept_repo.get_concept("{number}"), 
                   function_concept=concept_repo.get_concept("$+({new number}:{number})"), 
                   value_concepts=[concept_repo.get_concept("{new number}")], 
                   flow_info={"flow_index": "1.1.3", "support": ["1.1.3.1", "1.1.3.2"], "target": ["1.1"]}),

    # 1.1.3.1. Timing Gate: This becomes ready after a digit is extracted and grouped in a cycle. So the 1.3 can continue. 
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="timing", 
                   concept_to_infer=concept_repo.get_concept("$+({new number}:{number})"), 
                   function_concept=concept_repo.get_concept("@after([{index} and {digit}]*)"), 
                   value_concepts=[], 
                   flow_info={"flow_index": "1.1.3.1", "target": ["1.1.3"]}, start_without_value=True),

    # 1.1.3.2. Create the new number by removing the last digit. This depends on the timing gate.
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="imperative", 
                   concept_to_infer=concept_repo.get_concept("{new number}"), 
                   function_concept=concept_repo.get_concept("::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)"), 
                   value_concepts=[
                       concept_repo.get_concept("{unit place digit}?"), 
                       concept_repo.get_concept("{number}"), 
                       concept_repo.get_concept("@after([{index} and {digit}]*)")
                   ], 
                   flow_info={"flow_index": "1.1.3.2", "target": ["1.1.3"]}),

    # 1.1.4. Index Update Logic (also depends on the timing gate)
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="imperative", 
                   concept_to_infer=concept_repo.get_concept("{index}*"), 
                   function_concept=concept_repo.get_concept("::(increment {1}<$({index})%_> by 1)"), 
                   value_concepts=[
                       concept_repo.get_concept("{index}*"), 
                       concept_repo.get_concept("@after([{index} and {digit}]*)")
                   ], 
                   flow_info={"flow_index": "1.1.4", "support": ["1.1.4.1"], "target": ["1.1"]}),

    # 1.1.4.1. Timing Gate: This becomes ready after a digit is extracted and grouped in a cycle. So the 1.4 can continue. 
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="timing", 
                   concept_to_infer=concept_repo.get_concept("::(increment {1}<$({index})%_> by 1)"), 
                   function_concept=concept_repo.get_concept("@after([{index} and {digit}]*)"), 
                   value_concepts=[], 
                   flow_info={"flow_index": "1.1.4.1", "target": ["1.1.4"]}, start_without_value=True),
]
inference_repo = InferenceRepo(inference_entries) 

# --- Initial State Configuration ---
def configure_initial_state(concepts: List[ConceptEntry], inferences: List[InferenceEntry], 
                           initial_data_concepts: set[str], blackboard: Blackboard) -> set[str]:
    """
    Sets the initial reference_status for concepts in the Blackboard and returns a set of 'protected'
    concept names that should not be reset during orchestration cycles.
    """
    logging.info("--- Configuring Initial Concept States ---")
    
    inferred_concept_names = {inf.concept_to_infer.concept_name for inf in inferences}
    function_concept_names = {inf.function_concept.concept_name for inf in inferences if inf.function_concept}
    
    primitive_functions = function_concept_names - inferred_concept_names
    
    protected_concepts = primitive_functions.union(initial_data_concepts)
    
    for concept in concepts:
        if concept.concept_name in protected_concepts:
            blackboard.set_concept_status(concept.concept_name, 'complete')
            if concept.concept_name in primitive_functions:
                logging.info(f"Primitive function '{concept.concept_name}' set to 'complete'.")
            else:
                logging.info(f"Initial data concept '{concept.concept_name}' set to 'complete'.")
    
    logging.info(f"Identified {len(protected_concepts)} protected concepts that will not be reset.")
    return protected_concepts

# --- Orchestrator ---

class Orchestrator:
    """
    Orchestrates a waitlist of inferences, processing them in a bottom-up fashion
    based on the completion of their "support" dependencies.
    """
    def __init__(self, inference_repo: InferenceRepo, concept_repo: ConceptRepo, protected_concepts: set[str]):
        self.inference_repo = inference_repo
        self.concept_repo = concept_repo
        self.waitlist: Optional[Waitlist] = None
        
        # Centralized state management
        self.blackboard = Blackboard()
        
        # Process tracking
        self.tracker = ProcessTracker()
        
        # Use the pre-calculated set of protected concepts
        self.protected_concepts = protected_concepts
        
        # Automatically create the waitlist and initialize states on initialization
        self._create_waitlist_and_initialize_states()

        # Map inferred concepts to their waitlist items for easy lookup during resets
        self._item_by_inferred_concept: Dict[str, WaitlistItem] = {
            item.inference_entry.concept_to_infer.concept_name: item for item in self.waitlist.items
        }

    def _create_waitlist_and_initialize_states(self):
        """Creates a waitlist and initializes all concept and item states in the Blackboard."""
        items = [WaitlistItem(inference_entry=inf) for inf in self.inference_repo.get_all_inferences()]
        self.waitlist = Waitlist(id=str(uuid.uuid4()), items=items)
        
        # Initialize all states in the state manager
        self.blackboard.initialize_states(list(self.concept_repo._concept_map.values()), self.waitlist.items)
        
        logging.info(f"Created waitlist {self.waitlist.id} with {len(self.waitlist.items)} items and initialized states.")

    def _is_ready(self, item: WaitlistItem) -> bool:
        """
        An item is ready if its function concept is 'complete' and either:
        - Its `start_without_value` flag is True.
        - All its value concepts have a 'complete' reference status.
        - For '@after' scheduling, the concept it waits for is 'complete'.
        """
        fc = item.inference_entry.function_concept
        function_concept_ready = (fc is None) or (self.blackboard.get_concept_status(fc.concept_name) == 'complete')

        if not function_concept_ready:
            return False

        if item.inference_entry.start_without_value:
            return True
            
        # Special readiness check for '@after' timing concepts
        if fc and item.inference_entry.inference_sequence == 'timing' and fc.concept_name.startswith('@after('):
            match = re.search(r'@after\((.+)\)', fc.concept_name)
            if match:
                dependency_concept_name = match.group(1)
                return self.blackboard.get_concept_status(dependency_concept_name) == 'complete'
            return False # Malformed @after concept

        # Default readiness check for all other items
        return all(self.blackboard.get_concept_status(vc.concept_name) == 'complete' for vc in item.inference_entry.value_concepts)

    def _reset_non_protected_concepts(self):
        """Resets concept statuses and the status of items that inferred them."""
        resets = 0
        for concept_entry in self.concept_repo._concept_map.values():
            if concept_entry.concept_name not in self.protected_concepts and self.blackboard.get_concept_status(concept_entry.concept_name) == 'complete':
                self.blackboard.set_concept_status(concept_entry.concept_name, 'empty')
                resets += 1
                
                # Also reset the status of the item that inferred this concept
                item_to_reset = self._item_by_inferred_concept.get(concept_entry.concept_name)
                if item_to_reset:
                    flow_idx = item_to_reset.inference_entry.flow_info['flow_index']
                    if self.blackboard.get_item_status(flow_idx) == 'completed':
                        self.blackboard.set_item_status(flow_idx, 'pending')
                        logging.info(f"    -> Resetting dependent item {flow_idx} to 'pending'.")
        
        if resets > 0:
            logging.info(f"  -> Reset {resets} non-protected, complete concepts to 'empty'.")

    def _handle_quantifying_cycle(self, item: WaitlistItem) -> bool:
        """
        Handles the special state-reset logic for a 'quantifying' inference.
        Returns True if the item was handled and its status set to pending, False otherwise.
        """
        flow_index = item.inference_entry.flow_info['flow_index']
        execution_count = self.blackboard.get_execution_count(flow_index)

        if item.inference_entry.inference_sequence == 'quantifying' and execution_count <= 3:
            logging.info(f"  -> Quantifying item {flow_index} (exec #{execution_count}) is in progress. Resetting concepts.")
            self._reset_non_protected_concepts()
            self.blackboard.set_item_result(flow_index, "Pending (reset cycle)")
            return True
        return False

    def _inference_execution(self, item: WaitlistItem) -> str:
        """
        Simulates inference execution. 50% chance to complete, 50% chance to remain pending.
        If completed, it sets the inferred concept's reference status to 'complete'.
        Updates the item's result and returns the new status.
        Special logic for 'quantifying': must be executed 3 times, resetting state, before it can complete.
        """
        flow_index = item.inference_entry.flow_info['flow_index']
        self.blackboard.increment_execution_count(flow_index)

        # Special handling for 'quantifying' inferences that resets state
        if self._handle_quantifying_cycle(item):
            return "pending"
        
        # Simulate work
        time.sleep(0.05)
        
        if random.random() < 0.96:
            self.blackboard.set_item_result(flow_index, "Success")
            
            # On success, always update the concept_to_infer
            concept = item.inference_entry.concept_to_infer
            self.blackboard.set_concept_status(concept.concept_name, 'complete')
            logging.info(f"  -> Concept '{concept.concept_name}' set to 'complete'.")

            return "completed"
        else:
            self.blackboard.set_item_result(flow_index, "Pending")
            return "pending"

    def _execute_item(self, item: WaitlistItem) -> str:
        """Executes a single waitlist item and updates its status and tracking info."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"Item {flow_index} is ready. Executing.")
        
        self.blackboard.set_item_status(flow_index, 'in_progress')
        
        # Execute and get new status
        new_status = self._inference_execution(item)
        
        self.tracker.total_executions += 1
        
        self.blackboard.set_item_status(flow_index, new_status)
        
        # Track execution history
        self.tracker.add_execution_record(
            cycle=self.tracker.cycle_count,
            flow_index=flow_index,
            inference_type=item.inference_entry.inference_sequence,
            status=new_status,
            concept_inferred=item.inference_entry.concept_to_infer.concept_name
        )
        
        if new_status == 'completed':
            logging.info(f"Item {flow_index} COMPLETED.")
            self.tracker.successful_executions += 1
            self.tracker.record_completion(flow_index)
        else:
            logging.info(f"Item {flow_index} did not complete, will retry.")
            self.tracker.retry_count += 1
            
        return new_status

    def run(self):
        """Runs the orchestration loop until completion or deadlock."""
        if not self.waitlist:
            logging.error("No waitlist created. Call create_waitlist() first.")
            return

        logging.info(f"--- Starting Orchestration for Waitlist {self.waitlist.id} ---")
        
        retries: List[WaitlistItem] = []

        while self.blackboard.get_all_pending_or_in_progress_items():
            self.tracker.cycle_count += 1
            cycle_executions = 0
            cycle_successes = 0
            
            logging.info(f"--- Cycle {self.tracker.cycle_count} ---")
            
            next_cycle_retries: List[WaitlistItem] = []

            # Create a list of items to process, with retries first.
            # Using a set of retried items for an efficient lookup to avoid duplicates.
            retried_items_set = set(retries)
            items_to_process = retries + [
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

            retries = next_cycle_retries
            
            logging.info(f"Cycle {self.tracker.cycle_count}: {cycle_executions} executions, {cycle_successes} completions")
            
            if cycle_executions == 0:
                logging.warning("No progress made in the last cycle. Deadlock detected.")
                stuck_items = [i.inference_entry.flow_info['flow_index'] for i in self.waitlist.items if self.blackboard.get_item_status(i.inference_entry.flow_info['flow_index']) != 'completed']
                logging.warning(f"Stuck items: {stuck_items}")
                break
        
        logging.info(f"--- Orchestration Finished for Waitlist {self.waitlist.id} ---")

    def print_summary(self):
        if not self.waitlist: return
        
        print(f"\n=== Orchestration Summary (ID: {self.waitlist.id}) ===")
        
        # Status summary
        sorted_items = sorted(self.waitlist.items, key=lambda i: [int(p) for p in i.inference_entry.flow_info['flow_index'].split('.')])
        print("\n--- Item Status ---")
        for item in sorted_items:
            fi = item.inference_entry.flow_info['flow_index']
            it = item.inference_entry.inference_sequence
            status = self.blackboard.get_item_status(fi)
            print(f"  - Item {fi:<10} ({it:<12}): {status}")
        
        # Process statistics
        print(f"\n--- Process Statistics ---")
        print(f"  - Total cycles: {self.tracker.cycle_count}")
        print(f"  - Total executions: {self.tracker.total_executions}")
        print(f"  - Successful completions: {self.tracker.successful_executions}")
        print(f"  - Retry attempts: {self.tracker.retry_count}")
        print(f"  - Success rate: {self.tracker.get_success_rate():.1f}%")
        
        # Completion order
        print(f"\n--- Completion Order ---")
        for i, flow_index in enumerate(self.tracker.completion_order, 1):
            print(f"  {i:2d}. {flow_index}")
        
        # Execution flow
        print(f"\n--- Execution Flow ---")
        for record in self.tracker.execution_history:
            status_symbol = "✓" if record['status'] == 'completed' else "⟳"
            print(f"  Cycle {record['cycle']}: {status_symbol} {record['flow_index']} ({record['inference_type']}) -> {record['concept_inferred']}")

# --- Main Execution ---
if __name__ == "__main__":
    initial_data = {"{number}", "{unit place digit}?", "{index}*", "*every({number})%:[{number}]@[{index}^1]", "@after([{index} and {digit}]*)"}
    
    # The orchestrator now creates the state manager internally
    orchestrator = Orchestrator(inference_repo, concept_repo, set()) # Protected set is configured inside
    
    # Configure the initial state using the orchestrator's state manager
    protected_concepts = configure_initial_state(
        concept_entries, 
        inference_entries, 
        initial_data, 
        orchestrator.blackboard
    )
    orchestrator.protected_concepts = protected_concepts

    orchestrator.run()
    orchestrator.print_summary() 