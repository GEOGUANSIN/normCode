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
    # Truth masks from judgement inferences for filtering
    # concept_name -> {'tensor': [...], 'axes': [...], 'filter_axis': str}
    concept_truth_masks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Concept aliases for identity ($=) - maps alias_name -> canonical_name
    # When two concepts are merged via $=, both names resolve to the same canonical concept
    concept_aliases: Dict[str, str] = field(default_factory=dict)
    # Concept reset counts - tracks how many times a concept reference has been reset (loop iterations)
    concept_reset_counts: Dict[str, int] = field(default_factory=dict)

    def resolve_concept_name(self, concept_name: str) -> str:
        """
        Resolves a concept name through the alias chain to its canonical name.
        Used for identity ($=) operations that merge two concepts into one.
        """
        # Follow alias chain (handles transitive aliases: A→B→C)
        visited = set()
        current = concept_name
        while current in self.concept_aliases and current not in visited:
            visited.add(current)
            current = self.concept_aliases[current]
        return current

    def register_identity(self, concept_a: str, concept_b: str):
        """
        Registers an identity relationship: concept_a and concept_b are the SAME concept.
        Both names will resolve to a single canonical name.
        
        This is bidirectional - after registration, looking up either name
        will resolve to the same underlying concept.
        """
        # Resolve both to their current canonical forms
        canonical_a = self.resolve_concept_name(concept_a)
        canonical_b = self.resolve_concept_name(concept_b)
        
        if canonical_a == canonical_b:
            logging.debug(f"Identity: '{concept_a}' and '{concept_b}' already resolve to '{canonical_a}'")
            return
        
        # Choose canonical: prefer the one that already has status/data
        # If both have status, prefer the one that's 'complete'
        status_a = self.concept_statuses.get(canonical_a, "empty")
        status_b = self.concept_statuses.get(canonical_b, "empty")
        
        if status_b == "complete" and status_a != "complete":
            # B is more complete, make A point to B
            canonical, alias = canonical_b, canonical_a
        else:
            # Default: A is canonical, B points to A
            canonical, alias = canonical_a, canonical_b
        
        # Register the alias
        self.concept_aliases[alias] = canonical
        
        # Merge statuses: if either is complete, both are complete
        if status_a == "complete" or status_b == "complete":
            self.concept_statuses[canonical] = "complete"
        
        # Copy flow_index mapping if alias had one
        if alias in self.concept_to_flow_index and canonical not in self.concept_to_flow_index:
            self.concept_to_flow_index[canonical] = self.concept_to_flow_index[alias]
        
        logging.info(f"Identity registered: '{alias}' → '{canonical}' (both names now resolve to same concept)")

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
        canonical = self.resolve_concept_name(concept_name)
        return self.concept_statuses.get(canonical, "empty")

    def set_concept_status(self, concept_name: str, status: str):
        canonical = self.resolve_concept_name(concept_name)
        self.concept_statuses[canonical] = status
        if status == 'complete':
            if canonical not in self.completed_concept_timestamps:
                self.completed_concept_timestamps[canonical] = time.time()
                logging.info(f"  -> Blackboard: Recorded completion of '{canonical}'.")

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

    def get_concept_reset_count(self, concept_name: str) -> int:
        """Get the number of times a concept has been reset (loop iteration count)."""
        canonical = self.resolve_concept_name(concept_name)
        return self.concept_reset_counts.get(canonical, 0)

    def increment_concept_reset_count(self, concept_name: str):
        """Increment the reset count for a concept (called when entering a new loop iteration)."""
        canonical = self.resolve_concept_name(concept_name)
        self.concept_reset_counts[canonical] = self.get_concept_reset_count(canonical) + 1
        logging.debug(f"Concept '{canonical}' reset count incremented to {self.concept_reset_counts[canonical]}")

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
        """Checks if a concept's status is 'complete'. Resolves aliases automatically."""
        canonical = self.resolve_concept_name(concept_name)
        logging.info(f"Completed concepts for condition check '{concept_name}' (canonical: '{canonical}'): {self.get_completed_concepts()}")
        return self.get_concept_status(canonical) == 'complete'

    # --- Truth mask methods for filter injection ---

    def set_truth_mask(self, concept_name: str, truth_mask_data: Dict[str, Any]):
        """
        Store a truth mask from a judgement inference for use in filter injection.
        
        Args:
            concept_name: The judgement concept name (e.g., '<doc is relevant>')
            truth_mask_data: Dict containing:
                - 'tensor': The truth mask data (list of '%{truth value}(true/false)')
                - 'axes': List of axis names
                - 'filter_axis': The primary filter axis name (from for-each quantifier)
        """
        self.concept_truth_masks[concept_name] = truth_mask_data
        logging.info(f"Blackboard: Stored truth mask for '{concept_name}' with filter_axis='{truth_mask_data.get('filter_axis')}'")

    def get_truth_mask(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a truth mask for a judgement concept.
        
        Returns:
            Truth mask data dict or None if not found.
        """
        return self.concept_truth_masks.get(concept_name)

    def clear_truth_mask(self, concept_name: str):
        """Remove a truth mask (e.g., when concept is reset in a loop)."""
        if concept_name in self.concept_truth_masks:
            del self.concept_truth_masks[concept_name]
            logging.debug(f"Blackboard: Cleared truth mask for '{concept_name}'")

    # --- Serialization helpers for checkpointing ---

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the blackboard state to a dictionary."""
        return {
            "concept_statuses": self.concept_statuses.copy(),
            "item_statuses": self.item_statuses.copy(),
            "item_results": self.item_results.copy(),
            "item_execution_counts": self.item_execution_counts.copy(),
            "item_completion_details": self.item_completion_details.copy(),
            "completed_concept_timestamps": self.completed_concept_timestamps.copy(),
            # concept_to_flow_index is derivable, but keeping it makes restoration trivial.
            "concept_to_flow_index": self.concept_to_flow_index.copy(),
            # Truth masks for filter injection
            "concept_truth_masks": {k: v.copy() if isinstance(v, dict) else v 
                                    for k, v in self.concept_truth_masks.items()},
            # Concept aliases for identity ($=) merging
            "concept_aliases": self.concept_aliases.copy(),
            # Concept reset counts for iteration history tracking
            "concept_reset_counts": self.concept_reset_counts.copy(),
        }

    def load_from_dict(self, data: Dict[str, Any]):
        """Updates the blackboard state from a dictionary."""
        if not data:
            return
        self.concept_statuses.update(data.get("concept_statuses", {}))
        self.item_statuses.update(data.get("item_statuses", {}))
        self.item_results.update(data.get("item_results", {}))
        self.item_execution_counts.update(data.get("item_execution_counts", {}))
        self.item_completion_details.update(data.get("item_completion_details", {}))
        self.completed_concept_timestamps.update(data.get("completed_concept_timestamps", {}))
        self.concept_to_flow_index.update(data.get("concept_to_flow_index", {}))
        self.concept_truth_masks.update(data.get("concept_truth_masks", {}))
        self.concept_aliases.update(data.get("concept_aliases", {}))
        self.concept_reset_counts.update(data.get("concept_reset_counts", {}))
        logging.info("Blackboard state loaded from dictionary.")