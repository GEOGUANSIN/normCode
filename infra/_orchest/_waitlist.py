import logging
from dataclasses import dataclass
from typing import List
from infra._orchest._repo import InferenceEntry

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
