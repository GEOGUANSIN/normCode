import uuid
import logging
import os
import sys

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Import from waitlist_orchestrator ---
try:
    from waitlist_orchestrator import (
        ConceptEntry, InferenceEntry, WaitlistItem, Waitlist, ProcessTracker,
        ConceptRepo, InferenceRepo, configure_initial_state, Orchestrator
    )
except ImportError:
    # Add the current directory to path if import fails
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here))
    from waitlist_orchestrator import (
        ConceptEntry, InferenceEntry, WaitlistItem, Waitlist, ProcessTracker,
        ConceptRepo, InferenceRepo, configure_initial_state, Orchestrator
    )

# --- Data Definitions for Simple Example ---
concept_entries: list[ConceptEntry] = [
    ConceptEntry(id=str(uuid.uuid4()), concept_name="A", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="B", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="C", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="D", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="E", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="F", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="G", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="H", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="I", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="J", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="K", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="L", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="M", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="N", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="O", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="P", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="Q", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="R", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="S", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="T", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="U", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="V", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="W", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="X", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="Y", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="Z", type="object"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="*every({A})%:[{A}]@[{B}^1]", type="quantifying"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="$.([{C} and {D}]*)", type="assigning"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="&in({E}*;{F}*)", type="grouping"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="::(get {2}?<$({G})%_> of {1}<$({H})%_>)", type="imperative"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="@after(C)", type="scheduling"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="$+({K}:{L})", type="assigning"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="::(remove {2}?<$({M})%_> from {1}<$({N})%_>)", type="imperative"),
    ConceptEntry(id=str(uuid.uuid4()), concept_name="::(increment {1}<$({O})%_>)", type="imperative"),
]
concept_repo = ConceptRepo(concept_entries)

inference_entries: list[InferenceEntry] = [
    # Main quantifying inference
    InferenceEntry(
        id=str(uuid.uuid4()), 
        inference_sequence="quantifying", 
        concept_to_infer=concept_repo.get_concept("A"), 
        function_concept=concept_repo.get_concept("*every({A})%:[{A}]@[{B}^1]"), 
        value_concepts=[concept_repo.get_concept("B")], 
        flow_info={"flow_index": "1", "support": ["1.1", "1.2", "1.3"]}
    ),
    # Assigning inference
    InferenceEntry(
        id=str(uuid.uuid4()), 
        inference_sequence="assigning", 
        concept_to_infer=concept_repo.get_concept("*every({A})%:[{A}]@[{B}^1]"), 
        function_concept=concept_repo.get_concept("$.([{C} and {D}]*)"), 
        value_concepts=[concept_repo.get_concept("C"), concept_repo.get_concept("B"), concept_repo.get_concept("O")], 
        flow_info={"flow_index": "1.1", "support": ["1.1.1"], "target": ["1"]}
    ),
    # Grouping inference
    InferenceEntry(
        id=str(uuid.uuid4()), 
        inference_sequence="grouping", 
        concept_to_infer=concept_repo.get_concept("C"), 
        function_concept=concept_repo.get_concept("&in({E}*;{F}*)"), 
        value_concepts=[concept_repo.get_concept("O"), concept_repo.get_concept("F")], 
        flow_info={"flow_index": "1.1.1", "support": ["1.1.1.1"], "target": ["1.1"]}
    ),
    # Imperative inference
    InferenceEntry(
        id=str(uuid.uuid4()), 
        inference_sequence="imperative", 
        concept_to_infer=concept_repo.get_concept("F"), 
        function_concept=concept_repo.get_concept("::(get {2}?<$({G})%_> of {1}<$({H})%_>)"), 
        value_concepts=[concept_repo.get_concept("G"), concept_repo.get_concept("H")], 
        flow_info={"flow_index": "1.1.1.1", "target": ["1.1.1"]}
    ),
    # Scheduling inference
    InferenceEntry(
        id=str(uuid.uuid4()), 
        inference_sequence="scheduling", 
        concept_to_infer=concept_repo.get_concept("B"), 
        function_concept=concept_repo.get_concept("@after(C)"), 
        value_concepts=[], 
        flow_info={"flow_index": "1.2", "support": ["1.2.1"], "target": ["1.1.1.1"]}
    ),
    # Assigning inference
    InferenceEntry(
        id=str(uuid.uuid4()), 
        inference_sequence="assigning", 
        concept_to_infer=concept_repo.get_concept("@after(C)"), 
        function_concept=concept_repo.get_concept("$+({K}:{L})"), 
        value_concepts=[concept_repo.get_concept("L")], 
        flow_info={"flow_index": "1.2.1", "support": ["1.2.1.1"], "target": ["1.2"]}
    ),
    # Imperative inference
    InferenceEntry(
        id=str(uuid.uuid4()), 
        inference_sequence="imperative", 
        concept_to_infer=concept_repo.get_concept("L"), 
        function_concept=concept_repo.get_concept("::(remove {2}?<$({M})%_> from {1}<$({N})%_>)"), 
        value_concepts=[concept_repo.get_concept("M"), concept_repo.get_concept("N")], 
        flow_info={"flow_index": "1.2.1.1", "target": ["1.2.1"]}
    ),
    # Scheduling inference
    InferenceEntry(
        id=str(uuid.uuid4()), 
        inference_sequence="scheduling", 
        concept_to_infer=concept_repo.get_concept("O"), 
        function_concept=concept_repo.get_concept("@after(C)"), 
        value_concepts=[], 
        flow_info={"flow_index": "1.3", "support": ["1.3.1"], "target": ["1.1.1.1"]}
    ),
    # Imperative inference
    InferenceEntry(
        id=str(uuid.uuid4()), 
        inference_sequence="imperative", 
        concept_to_infer=concept_repo.get_concept("@after(C)"), 
        function_concept=concept_repo.get_concept("::(increment {1}<$({O})%_>)"), 
        value_concepts=[concept_repo.get_concept("O")], 
        flow_info={"flow_index": "1.3.1", "target": ["1.3"]}
    ),
]
inference_repo = InferenceRepo(inference_entries) 

# --- Main Execution ---
if __name__ == "__main__":
    print("=== Simple Orchestrator Example with Meaningless Symbols ===")
    print("This example demonstrates the orchestrator with concepts A, B, C, etc.")
    print("The flow follows a similar pattern to the original but with simplified names.\n")
    
    # Define the initial data concepts specific to this simple example
    initial_data_concepts = {"B", "G", "H", "M", "N", "O"}

    protected_concepts = configure_initial_state(concept_entries, inference_entries, initial_data_concepts)
    orchestrator = Orchestrator(inference_repo, concept_repo, protected_concepts)
    orchestrator.run()
    orchestrator.print_summary() 