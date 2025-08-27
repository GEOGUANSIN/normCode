import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class Blackboard:
    """Manages the dynamic state of all concepts and inference items."""
    concept_statuses: Dict[str, str] = field(default_factory=dict)  # concept_name -> status
    item_statuses: Dict[str, str] = field(default_factory=dict)     # flow_index -> status
    item_results: Dict[str, any] = field(default_factory=dict)      # flow_index -> result
    item_execution_counts: Dict[str, int] = field(default_factory=dict) # flow_index -> count
    completed_concept_timestamps: Dict[str, float] = field(default_factory=dict)  # concept_name -> timestamp

    def initialize_states(self, concepts: List[Any], items: List[Any]):
        """Sets the initial state for all concepts and items."""
        for concept in concepts:
            self.concept_statuses[concept.concept_name] = "empty"
        for item in items:
            flow_index = item.inference_entry.flow_info['flow_index']
            self.item_statuses[flow_index] = "pending"
            self.item_execution_counts[flow_index] = 0
            self.item_results[flow_index] = None

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

    def check_progress_condition(self, concept_name: str) -> bool:
        """Checks if a concept's status is 'complete'."""
        return self.get_concept_status(concept_name) == 'complete' 