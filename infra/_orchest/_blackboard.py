import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class Blackboard:
    """Manages the dynamic state of all concepts and inference items."""
    concept_statuses: Dict[str, str] = field(default_factory=dict)  # concept_name -> status
    item_statuses: Dict[str, str] = field(default_factory=dict)     # flow_index -> status
    item_results: Dict[str, any] = field(default_factory=dict)      # flow_index -> result
    item_execution_counts: Dict[str, int] = field(default_factory=dict) # flow_index -> count
    item_completion_details: Dict[str, str] = field(default_factory=dict) # flow_index -> 'success' or 'skipped'
    completed_concept_timestamps: Dict[str, float] = field(default_factory=dict)  # concept_name -> timestamp
    concept_to_flow_index: Dict[str, str] = field(default_factory=dict) # concept_name -> flow_index

    def initialize_states(self, concepts: List[Any], items: List[Any]):
        """Sets the initial state for all concepts and items."""
        for concept in concepts:
            self.concept_statuses[concept.concept_name] = "empty"
        for item in items:
            flow_index = item.inference_entry.flow_info['flow_index']
            self.item_statuses[flow_index] = "pending"
            self.item_execution_counts[flow_index] = 0
            self.item_results[flow_index] = None

            # Map the inferred concept to the item's flow index
            inferred_concept_name = item.inference_entry.concept_to_infer.concept_name
            self.concept_to_flow_index[inferred_concept_name] = flow_index

        # Set ground concepts to 'complete' status based on their is_ground_concept attribute
        for concept in concepts:
            if hasattr(concept, 'is_ground_concept') and concept.is_ground_concept:
                self.set_concept_status(concept.concept_name, 'complete')
                logging.info(f"Blackboard: Initial ground concept '{concept.concept_name}' set to 'complete'.")

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
        # Default to 'success' when an item is completed, can be overwritten.
        if status == 'completed':
            if self.get_item_completion_detail(flow_index) is None:
                self.set_item_completion_detail(flow_index, 'success')

    def get_item_result(self, flow_index: str) -> any:
        return self.item_results.get(flow_index)

    def set_item_result(self, flow_index: str, result: any):
        self.item_results[flow_index] = result

    def get_item_completion_detail(self, flow_index: str) -> Optional[str]:
        return self.item_completion_details.get(flow_index)

    def set_item_completion_detail(self, flow_index: str, detail: str):
        self.item_completion_details[flow_index] = detail

    def get_execution_count(self, flow_index: str) -> int:
        return self.item_execution_counts.get(flow_index, 0)

    def increment_execution_count(self, flow_index: str):
        self.item_execution_counts[flow_index] = self.get_execution_count(flow_index) + 1

    def reset_execution_count(self, flow_index: str):
        """Resets the execution count for a specific item to 0."""
        self.item_execution_counts[flow_index] = 0
        logging.debug(f"Execution count for item {flow_index} reset to 0.")

    def get_all_pending_or_in_progress_items(self) -> bool:
        return any(s in ['pending', 'in_progress'] for s in self.item_statuses.values())

    def get_completed_concepts(self) -> List[str]:
        return list(self.completed_concept_timestamps.keys())

    def get_completion_detail_for_concept(self, concept_name: str) -> Optional[str]:
        """Gets the completion detail ('success', 'skipped') for the item that inferred a concept."""
        flow_index = self.concept_to_flow_index.get(concept_name)
        if flow_index:
            return self.get_item_completion_detail(flow_index)
        return None

    def check_progress_condition(self, concept_name: str) -> bool:
        """Checks if a concept's status is 'complete'."""
        logging.info(f"Completed concepts for condition check '{concept_name}': {self.get_completed_concepts()}")
        return self.get_concept_status(concept_name) == 'complete' 