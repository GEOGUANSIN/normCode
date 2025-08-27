import uuid
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Infra Imports ---
try:
    from infra import Inference, Concept
except Exception:
    import pathlib
    import sys
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))
    from infra import Inference, Concept

# --- Orchestrator Imports ---
from waitlist_orchestrator import ConceptEntry, InferenceEntry

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
# Note: ConceptEntry and InferenceEntry are now imported from waitlist_orchestrator

# --- Data Definitions ---
def create_concept_entries() -> List[ConceptEntry]:
    """Creates the concept entries for this specific NormCode example."""
    return [
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

def create_inference_entries(concept_repo) -> List[InferenceEntry]:
    """Creates the inference entries for this specific NormCode example."""
    return [
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

def get_initial_data_concepts() -> Set[str]:
    """Returns the set of initial data concepts for this specific example."""
    return {"{number}", "{unit place digit}?", "{index}*", "*every({number})%:[{number}]@[{index}^1]", "@after([{index} and {digit}]*)"}

# --- Configuration Factory ---
class WaitlistConfig:
    """Factory class for creating waitlist configuration for this specific NormCode example."""
    
    @staticmethod
    def create_concept_entries() -> List[ConceptEntry]:
        """Creates concept entries for this example."""
        return create_concept_entries()
    
    @staticmethod
    def create_inference_entries(concept_repo) -> List[InferenceEntry]:
        """Creates inference entries for this example."""
        return create_inference_entries(concept_repo)
    
    @staticmethod
    def get_initial_data_concepts() -> Set[str]:
        """Gets initial data concepts for this example."""
        return get_initial_data_concepts()
    
    @staticmethod
    def get_normcode_example() -> str:
        """Gets the NormCode example string."""
        return Normcode_example

# --- Main Execution ---
if __name__ == "__main__":
    # Import the orchestrator functionality
    from waitlist_orchestrator import (
        create_repositories, 
        configure_initial_state, 
        Orchestrator
    )
    
    # Create repositories using the configuration
    concept_repo, inference_repo = create_repositories(WaitlistConfig)
    
    # Get initial data from configuration
    initial_data = WaitlistConfig.get_initial_data_concepts()
    
    # The orchestrator now creates the state manager internally
    orchestrator = Orchestrator(inference_repo, concept_repo, set()) # Protected set is configured inside
    
    # Configure the initial state using the orchestrator's state manager
    protected_concepts = configure_initial_state(
        concept_repo._concept_map.values(), 
        inference_repo.get_all_inferences(), 
        initial_data, 
        orchestrator.blackboard
    )
    orchestrator.protected_concepts = protected_concepts

    orchestrator.run()
    orchestrator.print_summary() 