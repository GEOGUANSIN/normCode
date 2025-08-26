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
    <= *every({number})%:[{number}]@[{index}^1]
        <= $.([{index} and {digit}]*)
        <- [{index} and {digit}]*
            <= &in({index}*;{digit}*)
            <- {index}*
            <- {unit place value}*
                <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)
                <- {unit place digit}?<:{2}>
                <- {number}<$={a}><:{1}>
        <- {number}<$={a}>
            <= @after([{index} and {digit}]*)
                <= $+({new number}:{number})
                <- {new number}
                    <= ::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)
                    <- {unit place digit}?<:{2}> 
                    <- {number}<$={a}><:{1}>
        <- {index}*
            <= @after([{index} and {digit}]*)
                <= ::(increment {1}<$({index})%_>)
                <- {index}*
    <- {number}<$={a}>
"""

# --- Data Structures ---

@dataclass
class ConceptEntry:
    id: str
    concept_name: str
    type: str
    reference_status: str = "empty"  # complete, incomplete, empty
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
    """Represents an inference waiting to be processed, tracking its multi-stage status."""
    inference_entry: InferenceEntry
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[any] = None
    execution_count: int = 0

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
    ConceptEntry(id=str(uuid.uuid4()), concept_name="::(increment {1}<$({index})%_>)", type="imperative"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="{number}", type="object")
]
concept_repo = ConceptRepo(concept_entries)

inference_entries: List[InferenceEntry] = [
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="quantifying", concept_to_infer=concept_repo.get_concept("[all {index} and {digit} of number]"), function_concept=concept_repo.get_concept("*every({number})%:[{number}]@[{index}^1]"), value_concepts=[concept_repo.get_concept("{number}")], flow_info={"flow_index": "1", "support": ["1.1", "1.2", "1.3"]}, start_without_value=True),
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="assigning", concept_to_infer=concept_repo.get_concept("*every({number})%:[{number}]@[{index}^1]"), function_concept=concept_repo.get_concept("$.([{index} and {digit}]*)"), value_concepts=[concept_repo.get_concept("[{index} and {digit}]*"), concept_repo.get_concept("{number}"), concept_repo.get_concept("{index}*")], flow_info={"flow_index": "1.1", "support": ["1.1.1"], "target": ["1"]}),
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="grouping", concept_to_infer=concept_repo.get_concept("[{index} and {digit}]*"), function_concept=concept_repo.get_concept("&in({index}*;{digit}*)"), value_concepts=[concept_repo.get_concept("{index}*"), concept_repo.get_concept("{unit place value}*")], flow_info={"flow_index": "1.1.1", "support": ["1.1.1.1"], "target": ["1.1"]}),
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="imperative", concept_to_infer=concept_repo.get_concept("{unit place value}*"), function_concept=concept_repo.get_concept("::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)",), value_concepts=[concept_repo.get_concept("{unit place digit}?"), concept_repo.get_concept("{number}")], flow_info={"flow_index": "1.1.1.1", "target": ["1.1.1"]}),
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="timing", concept_to_infer=concept_repo.get_concept("{number}"), function_concept=concept_repo.get_concept("@after([{index} and {digit}]*)"), value_concepts=[], flow_info={"flow_index": "1.2", "support": ["1.2.1"], "target": ["1.1.1.1"]}, start_without_value=True),
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="assigning", concept_to_infer=concept_repo.get_concept("@after([{index} and {digit}]*)"), function_concept=concept_repo.get_concept("$+({new number}:{number})"), value_concepts=[concept_repo.get_concept("{new number}")], flow_info={"flow_index": "1.2.1", "support": ["1.2.1.1"], "target": ["1.2"]}),
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="imperative", concept_to_infer=concept_repo.get_concept("{new number}"), function_concept=concept_repo.get_concept("::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)",), value_concepts=[concept_repo.get_concept("{unit place digit}?"), concept_repo.get_concept("{number}")], flow_info={"flow_index": "1.2.1.1", "target": ["1.2.1"]}),
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="timing", concept_to_infer=concept_repo.get_concept("{index}*"), function_concept=concept_repo.get_concept("@after([{index} and {digit}]*)"), value_concepts=[], flow_info={"flow_index": "1.3", "support": ["1.3.1"], "target": ["1.1.1.1"]}, start_without_value=True),
    InferenceEntry(id=str(uuid.uuid4()), inference_sequence="imperative", concept_to_infer=concept_repo.get_concept("@after([{index} and {digit}]*)"), function_concept=concept_repo.get_concept("::(increment {1}<$({index})%_>)"), value_concepts=[concept_repo.get_concept("{index}*")], flow_info={"flow_index": "1.3.1", "target": ["1.3"]})
]
inference_repo = InferenceRepo(inference_entries) 

# --- Initial State Configuration ---
def configure_initial_state(concepts: List[ConceptEntry], inferences: List[InferenceEntry], initial_data_concepts: set[str]) -> set[str]:
    """
    Sets the initial reference_status for concepts and returns a set of 'protected'
    concept names that should not be reset during orchestration cycles.
    """
    logging.info("--- Configuring Initial Concept States ---")
    
    inferred_concept_names = {inf.concept_to_infer.concept_name for inf in inferences}
    function_concept_names = {inf.function_concept.concept_name for inf in inferences if inf.function_concept}
    
    primitive_functions = function_concept_names - inferred_concept_names
    
    protected_concepts = primitive_functions.union(initial_data_concepts)
    
    for concept in concepts:
        if concept.concept_name in protected_concepts:
            concept.reference_status = 'complete'
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
        self.item_status_by_flow: Dict[str, str] = {}
        
        # Process tracking
        self.tracker = ProcessTracker()
        
        # Use the pre-calculated set of protected concepts
        self.protected_concepts = protected_concepts
        
        # Automatically create the waitlist on initialization
        self._create_waitlist()

        # Map inferred concepts to their waitlist items for easy lookup during resets
        self._item_by_inferred_concept: Dict[str, WaitlistItem] = {
            item.inference_entry.concept_to_infer.concept_name: item for item in self.waitlist.items
        }

    def _create_waitlist(self) -> Waitlist:
        """Creates a waitlist from the inference repository."""
        items = [WaitlistItem(inference_entry=inf) for inf in self.inference_repo.get_all_inferences()]
        self.waitlist = Waitlist(id=str(uuid.uuid4()), items=items)
        self.item_status_by_flow = {item.inference_entry.flow_info['flow_index']: item.status for item in self.waitlist.items}
        logging.info(f"Created waitlist {self.waitlist.id} with {len(self.waitlist.items)} items.")
        return self.waitlist

    def _is_ready(self, item: WaitlistItem) -> bool:
        """
        An item is ready if its function concept is 'complete' and either:
        - Its `start_without_value` flag is True.
        - All its value concepts have a 'complete' reference status.
        - For '@after' scheduling, the concept it waits for is 'complete'.
        """
        fc = item.inference_entry.function_concept
        function_concept_ready = (fc is None) or (fc.reference_status == 'complete')

        if not function_concept_ready:
            return False

        if item.inference_entry.start_without_value:
            return True
            
        # Special readiness check for '@after' timing concepts
        if fc and item.inference_entry.inference_sequence == 'timing' and fc.concept_name.startswith('@after('):
            match = re.search(r'@after\((.+)\)', fc.concept_name)
            if match:
                dependency_concept_name = match.group(1)
                dependency_concept = self.concept_repo.get_concept(dependency_concept_name)
                return dependency_concept and dependency_concept.reference_status == 'complete'
            return False # Malformed @after concept

        # Default readiness check for all other items
        return all(vc.reference_status == 'complete' for vc in item.inference_entry.value_concepts)

    def _reset_non_protected_concepts(self):
        """Resets concept statuses and the status of items that inferred them."""
        resets = 0
        for concept_entry in self.concept_repo._concept_map.values():
            if concept_entry.concept_name not in self.protected_concepts and concept_entry.reference_status == 'complete':
                concept_entry.reference_status = 'empty'
                resets += 1
                
                # Also reset the status of the item that inferred this concept
                item_to_reset = self._item_by_inferred_concept.get(concept_entry.concept_name)
                if item_to_reset and item_to_reset.status == 'completed':
                    item_to_reset.status = 'pending'
                    flow_idx = item_to_reset.inference_entry.flow_info['flow_index']
                    self.item_status_by_flow[flow_idx] = 'pending'
                    logging.info(f"    -> Resetting dependent item {flow_idx} to 'pending'.")
        
        if resets > 0:
            logging.info(f"  -> Reset {resets} non-protected, complete concepts to 'empty'.")

    def _handle_quantifying_cycle(self, item: WaitlistItem) -> bool:
        """
        Handles the special state-reset logic for a 'quantifying' inference.
        Returns True if the item was handled and its status set to pending, False otherwise.
        """
        if item.inference_entry.inference_sequence == 'quantifying' and item.execution_count <= 3:
            flow_index = item.inference_entry.flow_info['flow_index']
            logging.info(f"  -> Quantifying item {flow_index} (exec #{item.execution_count}) is in progress. Resetting concepts.")
            self._reset_non_protected_concepts()
            item.result = "Pending (reset cycle)"
            return True
        return False

    def _inference_execution(self, item: WaitlistItem) -> str:
        """
        Simulates inference execution. 50% chance to complete, 50% chance to remain pending.
        If completed, it sets the inferred concept's reference status to 'complete'.
        Updates the item's result and returns the new status.
        Special logic for 'quantifying': must be executed 3 times, resetting state, before it can complete.
        """
        item.execution_count += 1

        # Special handling for 'quantifying' inferences that resets state
        if self._handle_quantifying_cycle(item):
            return "pending"
        
        # Simulate work
        time.sleep(0.05)
        
        if random.random() < 0.96:
            item.result = "Success"
            
            # On success, always update the concept_to_infer
            concept = item.inference_entry.concept_to_infer
            concept.reference_status = 'complete'
            logging.info(f"  -> Concept '{concept.concept_name}' set to 'complete'.")

            return "completed"
        else:
            item.result = "Pending"
            return "pending"

    def _execute_item(self, item: WaitlistItem) -> str:
        """Executes a single waitlist item and updates its status and tracking info."""
        flow_index = item.inference_entry.flow_info['flow_index']
        logging.info(f"Item {flow_index} is ready. Executing.")
        
        item.status = 'in_progress'
        self.item_status_by_flow[flow_index] = 'in_progress'
        
        # Execute and get new status
        new_status = self._inference_execution(item)
        
        self.tracker.total_executions += 1
        
        item.status = new_status
        self.item_status_by_flow[flow_index] = new_status
        
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

        while any(item.status in ['pending', 'in_progress'] for item in self.waitlist.items):
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
                if item.status == 'pending' and self._is_ready(item):
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
                stuck_items = [i.inference_entry.flow_info['flow_index'] for i in self.waitlist.items if i.status != 'completed']
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
            print(f"  - Item {fi:<10} ({it:<12}): {item.status}")
        
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
    protected_concepts = configure_initial_state(concept_entries, inference_entries, initial_data)
    orchestrator = Orchestrator(inference_repo, concept_repo, protected_concepts)
    orchestrator.run()
    orchestrator.print_summary() 