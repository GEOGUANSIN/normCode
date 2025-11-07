"""
Simple example demonstrating how to use the refactored waitlist orchestrator
with a custom configuration.
"""

import uuid
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set

# Import the orchestrator components
from waitlist_orchestrator import (
    Orchestrator, ConceptRepo, InferenceRepo, 
    WaitlistItem, configure_initial_state
)

# Import the data structures
from waitlist_config import ConceptEntry, InferenceEntry

# --- Simple Configuration Example ---

class SimpleWaitlistConfig:
    """A simple configuration for demonstration purposes."""
    
    @staticmethod
    def create_concept_entries() -> List[ConceptEntry]:
        """Creates a simple set of concept entries."""
        return [
            ConceptEntry(id=str(uuid.uuid4()), concept_name="A", type="object"),
            ConceptEntry(id=str(uuid.uuid4()), concept_name="B", type="object"),
            ConceptEntry(id=str(uuid.uuid4()), concept_name="C", type="object"),
            ConceptEntry(id=str(uuid.uuid4()), concept_name="add", type="imperative"),
            ConceptEntry(id=str(uuid.uuid4()), concept_name="result", type="object"),
        ]
    
    @staticmethod
    def create_inference_entries(concept_repo) -> List[InferenceEntry]:
        """Creates a simple inference chain: A + B -> result."""
        return [
            InferenceEntry(
                id=str(uuid.uuid4()), 
                inference_sequence="imperative",
                concept_to_infer=concept_repo.get_concept("result"),
                function_concept=concept_repo.get_concept("add"),
                value_concepts=[
                    concept_repo.get_concept("A"),
                    concept_repo.get_concept("B")
                ],
                flow_info={"flow_index": "1", "target": []}
            ),
            InferenceEntry(
                id=str(uuid.uuid4()), 
                inference_sequence="assigning",
                concept_to_infer=concept_repo.get_concept("C"),
                function_concept=None,
                value_concepts=[concept_repo.get_concept("result")],
                flow_info={"flow_index": "2", "target": []}
            )
        ]
    
    @staticmethod
    def get_initial_data_concepts() -> Set[str]:
        """Returns the initial data concepts."""
        return {"A", "B", "add"}

def create_simple_repositories():
    """Creates repositories for the simple example."""
    concept_entries = SimpleWaitlistConfig.create_concept_entries()
    concept_repo = ConceptRepo(concept_entries)
    inference_entries = SimpleWaitlistConfig.create_inference_entries(concept_repo)
    inference_repo = InferenceRepo(inference_entries)
    return concept_repo, inference_repo

def main():
    """Run the simple example."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("=== Simple Waitlist Example ===")
    
    # Create repositories using the simple configuration
    concept_repo, inference_repo = create_simple_repositories()
    
    # Get initial data from configuration
    initial_data = SimpleWaitlistConfig.get_initial_data_concepts()
    
    # Create orchestrator
    orchestrator = Orchestrator(inference_repo, concept_repo, set())
    
    # Configure initial state
    protected_concepts = configure_initial_state(
        concept_repo._concept_map.values(),
        inference_repo.get_all_inferences(),
        initial_data,
        orchestrator.blackboard
    )
    orchestrator.protected_concepts = protected_concepts
    
    # Run orchestration
    orchestrator.run()
    orchestrator.print_summary()

if __name__ == "__main__":
    main() 