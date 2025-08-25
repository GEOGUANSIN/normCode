import uuid
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Dict

# Configure logging to show DEBUG messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# Ensure this directory is importable regardless of where the script is run from
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import core components
try:
	from infra import Inference, Concept, Reference
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
	from infra import Inference, Concept, Reference

@dataclass
class ConceptEntry:
    """Dataclass representing a concept entry in the concept list."""
    id: str
    concept_name: str
    type: str
    concept: Optional[Concept] = None # Optional actual Concept instance
    description: Optional[str] = None

@dataclass
class Plan:
    """Represents an execution plan consisting of a sequence of moments."""
    id: str
    moments: List['Moment']
    created_at: float
    status: str = "pending"  # "pending", "in_progress", "completed", "failed"

class Orchestrator:
    """A simplified orchestrator to plan and execute a sequence of inferences."""

    def __init__(self, inference_repo: 'InferenceRepo'):
        self.inference_repo = inference_repo
        self.execution_history: List[Moment] = []
        self.task_history: List[Task] = []

    def plan(self) -> Plan:
        """Create an execution plan for all inferences from the repository."""
        moments = []
        for inference_entry in self.inference_repo.get_all_inferences():
            moment = Moment(inference_entry=inference_entry)
            moments.append(moment)
        
        plan = Plan(
            id=str(uuid.uuid4()),
            moments=moments,
            created_at=time.time()
        )
        logging.info(f"Created plan {plan.id} with {len(plan.moments)} moments.")
        return plan

    def show_plan(self, plan: Plan):
        """Display the moments of a given plan."""
        print(f"\n=== Execution Plan (ID: {plan.id}) ===")
        for i, moment in enumerate(plan.moments):
            print(f"\nStep {i+1}: {moment.inference_entry.inference_sequence}")
            print(f"  Concept: {moment.inference_entry.concept_to_infer.concept_name}")
            print(f"  Type: {moment.inference_entry.concept_to_infer.type}")
            if moment.inference_entry.function_concept:
                print(f"  Function: {moment.inference_entry.function_concept.concept_name}")
            print(f"  Flow Index: {moment.inference_entry.flow_info.get('flow_index', 'N/A')}")
            if moment.inference_entry.flow_info.get('target'):
                print(f"  Target: {moment.inference_entry.flow_info['target']}")
            if moment.inference_entry.flow_info.get('support'):
                print(f"  Support: {moment.inference_entry.flow_info['support']}")
            
            # Show the four tasks for this inference
            tasks = TaskManager.create_tasks_for_inference(moment.inference_entry)
            print(f"  Tasks:")
            for task in tasks:
                print(f"    - {task.task_type}: {TaskManager.get_task_description(task.task_type)}")
        print("==========================================")

    def execute_task(self, task: Task) -> bool:
        """Execute a single task for an inference."""
        task.status = "in_progress"
        
        try:
            if task.task_type == "check_support":
                # Check if dependencies are met
                target = task.inference_entry.flow_info.get('target', [])
                if target:
                    # In a real implementation, check if target inferences are completed
                    task.result = f"Support check passed. Targets: {target}"
                else:
                    task.result = "No dependencies to check"
                    
            elif task.task_type == "configure":
                # Configure the inference with parameters
                task.result = f"Configured inference: {task.inference_entry.inference_sequence}"
                
            elif task.task_type == "execute":
                # Execute the actual inference
                inference_instance = self.inference_repo.get_or_create_inference_instance(task.inference_entry.id)
                if inference_instance:
                    # In a real scenario, you'd call: result = inference_instance.execute()
                    task.result = f"Executed inference: {task.inference_entry.inference_sequence}"
                else:
                    task.result = "No inference instance to execute"
                    
            elif task.task_type == "contribute":
                # Contribute the result to the overall computation
                task.result = f"Contributed result from: {task.inference_entry.inference_sequence}"
            
            task.status = "completed"
            return True
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logging.error(f"Task {task.task_type} failed for {task.inference_entry.inference_sequence}: {e}")
            return False

    def execute_plan(self, plan: Plan):
        """Execute a specific plan of moments with all four tasks per inference."""
        plan.status = "in_progress"
        
        logging.info(f"--- Starting Execution of Plan {plan.id} ---")
        
        for moment in plan.moments:
            logging.info(f"Processing inference: {moment.inference_entry.inference_sequence}")
            
            # Create and execute all four tasks for this inference
            tasks = TaskManager.create_tasks_for_inference(moment.inference_entry)
            
            all_tasks_successful = True
            for task in tasks:
                success = self.execute_task(task)
                self.task_history.append(task)
                
                if not success:
                    all_tasks_successful = False
                    moment.status = "failed"
                    moment.error = f"Task {task.task_type} failed: {task.error}"
                    break
            
            if all_tasks_successful:
                moment.status = "completed"
                moment.result = "All tasks completed successfully"
            
            self.execution_history.append(moment)
        
        if any(m.status == 'failed' for m in plan.moments):
            plan.status = "failed"
        else:
            plan.status = "completed"

        logging.info(f"--- Finished Execution of Plan {plan.id} ---")

    def print_summary(self):
        """Print a summary of the execution history."""
        print("\n=== Orchestrator Execution Summary ===")
        for i, moment in enumerate(self.execution_history):
            print(f"\nStep {i+1}: {moment.inference_entry.inference_sequence} on '{moment.inference_entry.concept_to_infer.concept_name}'")
            print(f"  Status: {moment.status}")
            if moment.status == 'completed':
                print(f"  Result: {moment.result}")
            elif moment.status == 'failed':
                print(f"  Error: {moment.error}")
            
            # Show task details for this moment
            moment_tasks = [t for t in self.task_history if t.inference_entry.id == moment.inference_entry.id]
            if moment_tasks:
                print(f"  Tasks:")
                for task in moment_tasks:
                    status_icon = "✓" if task.status == "completed" else "✗" if task.status == "failed" else "○"
                    print(f"    {status_icon} {task.task_type}: {task.status}")
                    if task.result:
                        print(f"      Result: {task.result}")
                    if task.error:
                        print(f"      Error: {task.error}")
        
        completed_count = len([m for m in self.execution_history if m.status == 'completed'])
        failed_count = len([m for m in self.execution_history if m.status == 'failed'])
        print("\n-------------------------------------")
        print(f"Total Executed: {len(self.execution_history)}")
        print(f"Completed: {completed_count}, Failed: {failed_count}")
        print("=====================================")

@dataclass
class InferenceEntry:
    """Dataclass representing an inference entry in the inference list."""
    id: str
    inference_sequence: str
    concept_to_infer: ConceptEntry
    function_concept: Optional[ConceptEntry]
    value_concepts: List[ConceptEntry]
    flow_info: Dict[str, any]
    inference: Optional[Inference] = None  # Optional actual Inference instance

class ConceptRepo:
    """Repository class to manage and retrieve concepts."""
    
    def __init__(self, concepts: List[ConceptEntry]):
        self.concepts = concepts
        self._concept_map = {concept.concept_name: concept for concept in concepts}
    
    def get_concept(self, concept_name: str) -> Optional[ConceptEntry]:
        """Get a concept by its name."""
        return self._concept_map.get(concept_name)
    
    def get_concepts_by_type(self, concept_type: str) -> List[ConceptEntry]:
        """Get all concepts of a specific type."""
        return [concept for concept in self.concepts if concept.type == concept_type]
    
    def get_all_concepts(self) -> List[ConceptEntry]:
        """Get all concepts."""
        return self.concepts.copy()
    
    def concept_exists(self, concept_name: str) -> bool:
        """Check if a concept exists by name."""
        return concept_name in self._concept_map
    
    def get_concept_names(self) -> List[str]:
        """Get all concept names."""
        return list(self._concept_map.keys())


@dataclass
class Moment:
    """Represents a single step in an execution plan."""
    inference_entry: InferenceEntry
    status: str = "pending"  # "pending", "completed", "failed"
    result: Optional[any] = None
    error: Optional[str] = None

@dataclass
class Task:
    """Represents a task that surrounds an inference execution."""
    id: str
    task_type: str  # "check_support", "configure", "execute", "contribute"
    inference_entry: InferenceEntry
    status: str = "pending"  # "pending", "in_progress", "completed", "failed"
    result: Optional[any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, any]] = None

class TaskManager:
    """Manages the four types of tasks for each inference."""
    
    TASK_TYPES = {
        "check_support": "Check if the inference has proper support and dependencies",
        "configure": "Configure the inference with necessary parameters and context",
        "execute": "Execute the actual inference logic",
        "contribute": "Contribute the inference result to the overall computation"
    }
    
    @staticmethod
    def create_tasks_for_inference(inference_entry: InferenceEntry) -> List[Task]:
        """Create all four tasks for a given inference entry."""
        tasks = []
        for task_type in TaskManager.TASK_TYPES.keys():
            task = Task(
                id=str(uuid.uuid4()),
                task_type=task_type,
                inference_entry=inference_entry
            )
            tasks.append(task)
        return tasks
    
    @staticmethod
    def get_task_description(task_type: str) -> str:
        """Get the description for a task type."""
        return TaskManager.TASK_TYPES.get(task_type, "Unknown task type")

class InferenceRepo:
    """Repository class to manage and retrieve inferences."""
    
    def __init__(self, inferences: List[InferenceEntry]):
        self.inferences = inferences
        self._inference_map = {inference.id: inference for inference in inferences}
        self._sequence_map = {}
        for inference in inferences:
            if inference.inference_sequence not in self._sequence_map:
                self._sequence_map[inference.inference_sequence] = []
            self._sequence_map[inference.inference_sequence].append(inference)
    
    def get_inference(self, inference_id: str) -> Optional[InferenceEntry]:
        """Get an inference by its ID."""
        return self._inference_map.get(inference_id)
    
    def get_inferences_by_sequence(self, sequence_type: str) -> List[InferenceEntry]:
        """Get all inferences of a specific sequence type."""
        return self._sequence_map.get(sequence_type, [])
    
    def get_all_inferences(self) -> List[InferenceEntry]:
        """Get all inferences."""
        return self.inferences.copy()
    
    def get_inferences_by_flow_index(self, flow_index: str) -> List[InferenceEntry]:
        """Get all inferences with a specific flow index."""
        return [inf for inf in self.inferences if inf.flow_info.get("flow_index") == flow_index]
    
    def get_inferences_by_concept_type(self, concept_type: str) -> List[InferenceEntry]:
        """Get all inferences where the concept to infer is of a specific type."""
        return [inf for inf in self.inferences if inf.concept_to_infer.type == concept_type]
    
    def get_inference_ids(self) -> List[str]:
        """Get all inference IDs."""
        return list(self._inference_map.keys())
    
    def get_sequence_types(self) -> List[str]:
        """Get all sequence types."""
        return list(self._sequence_map.keys())
    
    def create_inference_instance(self, inference_entry: InferenceEntry) -> Inference:
        """Create an Inference instance for an InferenceEntry that doesn't have one."""
        if inference_entry.inference is not None:
            return inference_entry.inference
        
        # Create new Inference instance
        inference = Inference(
            sequence_name=inference_entry.inference_sequence,
            concept_to_infer=inference_entry.concept_to_infer.concept,
            value_concepts=[vc.concept for vc in inference_entry.value_concepts],
            function_concept=inference_entry.function_concept.concept if inference_entry.function_concept else None
        )
        
        # Update the entry with the new inference instance
        inference_entry.inference = inference
        return inference
    
    def get_or_create_inference_instance(self, inference_id: str) -> Optional[Inference]:
        """Get or create an Inference instance for an inference entry."""
        inference_entry = self.get_inference(inference_id)
        if inference_entry is None:
            return None
        
        return self.create_inference_instance(inference_entry)
    
    def get_inferences_with_instances(self) -> List[InferenceEntry]:
        """Get all inference entries that have Inference instances."""
        return [inf for inf in self.inferences if inf.inference is not None]
    
    def get_inferences_without_instances(self) -> List[InferenceEntry]:
        """Get all inference entries that don't have Inference instances."""
        return [inf for inf in self.inferences if inf.inference is None]

# --- Normcode for this example ---

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


concept_entries: List[ConceptEntry] = [
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="[all {index} and {digit} of number]",
        type="object",
        concept=Concept("[all {index} and {digit} of number]"),
        description="Main loop that iterates through all index and digit pairs of a number"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="*every({number})%:[{number}]@[{index}^1]",
        type="quantifying",
        concept=Concept("*every({number})%:[{number}]@[{index}^1]"),
        description="Quantifier that processes every element in a number with index tracking"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="$.([{index} and {digit}]*)",
        type="assigning",
        concept=Concept("$.([{index} and {digit}]*)"),
        description="Assignment operation that creates pairs of index and digit"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="[{index} and {digit}]*",
        type="grouping",
        concept=Concept("[{index} and {digit}]*"),
        description="Group containing index and digit pairs"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="&in({index}*;{digit}*)",
        type="grouping",
        concept=Concept("&in({index}*;{digit}*)"),
        description="Grouping operation that combines index and digit collections"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="{index}*",
        type="object",
        concept=Concept("{index}*"),
        description="Collection of indices"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="{unit place value}*",
        type="object",
        concept=Concept("{unit place value}*"),
        description="Collection of unit place values"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)",
        type="imperative",
        concept=Concept("::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)"),
        description="Imperative operation to extract unit place digit from a number"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="{unit place digit}?",
        type="object",
        concept=Concept("{unit place digit}?"),
        description="Optional unit place digit with explanatory reference"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="@after([{index} and {digit}]*)",
        type="scheduling",
        concept=Concept("@after([{index} and {digit}]*)"),
        description="Scheduling operation that executes after index-digit processing"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="$+({new number}:{number})",
        type="assigning",
        concept=Concept("$+({new number}:{number})"),
        description="Assignment operation that creates a new number from existing number"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="{new number}",
        type="object",
        concept=Concept("{new number}"),
        description="Modified number after processing"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)",
        type="imperative",
        concept=Concept("::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)"),
        description="Imperative operation to remove a digit from a number"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="::(increment {1}<$({index})%_>)",
        type="imperative",
        concept=Concept("::(increment {1}<$({index})%_>)"),
        description="Imperative operation to increment an index"
    ),
    ConceptEntry(
        id=str(uuid.uuid4()),
        concept_name="{number}",
        type="object",
        concept=Concept("{number}"),
        description="Base number being processed"
    )
]

# Create the concept repository
concept_repo = ConceptRepo(concept_entries)


inference_entries: List[InferenceEntry] = [
    InferenceEntry(
        id=str(uuid.uuid4()),
        inference_sequence="quantifying",
        concept_to_infer=concept_repo.get_concept("[all {index} and {digit} of number]"),
        function_concept=concept_repo.get_concept("*every({number})%:[{number}]@[{index}^1]"),
        value_concepts=[concept_repo.get_concept("{number}")],
        flow_info={
            "flow_index": "1",
            "support": ["1.1", "1.2", "1.3"]
        },
        inference=Inference(
            sequence_name="quantifying",
            concept_to_infer=concept_repo.get_concept("[all {index} and {digit} of number]").concept,
            value_concepts=[concept_repo.get_concept("{number}").concept],
            function_concept=concept_repo.get_concept("*every({number})%:[{number}]@[{index}^1]").concept
        )
    ),
    InferenceEntry(
        id=str(uuid.uuid4()),
        inference_sequence="assigning",
        concept_to_infer=concept_repo.get_concept("*every({number})%:[{number}]@[{index}^1]"),
        function_concept=concept_repo.get_concept("$.([{index} and {digit}]*)"),
        value_concepts=[concept_repo.get_concept("[{index} and {digit}]*")],
        flow_info={
            "flow_index": "1.1",
            "support": ["1.1.1"],
            "target": ["1"]
        },
        inference=Inference(
            sequence_name="assigning",
            concept_to_infer=concept_repo.get_concept("*every({number})%:[{number}]@[{index}^1]").concept,
            value_concepts=[concept_repo.get_concept("[{index} and {digit}]*").concept],
            function_concept=concept_repo.get_concept("$.([{index} and {digit}]*)").concept
        )
    ),
    InferenceEntry(
        id=str(uuid.uuid4()),
        inference_sequence="grouping",
        concept_to_infer=concept_repo.get_concept("[{index} and {digit}]*"),
        function_concept=concept_repo.get_concept("&in({index}*;{digit}*)"),
        value_concepts=[concept_repo.get_concept("{index}*"), concept_repo.get_concept("{unit place value}*")],
        flow_info={
            "flow_index": "1.1.1",
            "support": ["1.1.1.1"],
            "target": ["1.1"]
        }
        # No inference instance for this entry (optional)
    ),
    InferenceEntry(
        id=str(uuid.uuid4()),
        inference_sequence="imperative",
        concept_to_infer=concept_repo.get_concept("{unit place value}*"),
        function_concept=concept_repo.get_concept("::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)"),
        value_concepts=[concept_repo.get_concept("{unit place digit}?"), concept_repo.get_concept("{number}")],
        flow_info={
            "flow_index": "1.1.1.1",
            "target": ["1.1.1"]
        },
        inference=Inference(
            sequence_name="imperative",
            concept_to_infer=concept_repo.get_concept("{unit place value}*").concept,
            value_concepts=[concept_repo.get_concept("{unit place digit}?").concept, concept_repo.get_concept("{number}").concept],
            function_concept=concept_repo.get_concept("::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)").concept
        )
    ),
    InferenceEntry(
        id=str(uuid.uuid4()),
        inference_sequence="scheduling",
        concept_to_infer=concept_repo.get_concept("{number}"),
        function_concept=concept_repo.get_concept("@after([{index} and {digit}]*)"),
        value_concepts=[concept_repo.get_concept("$+({new number}:{number})")],
        flow_info={
            "flow_index": "1.2",
            "support": ["1.2.1"],
            "target": ["1.1.1.1"]
        }
        # No inference instance for this entry (optional)
    ),
    InferenceEntry(
        id=str(uuid.uuid4()),
        inference_sequence="assigning",
        concept_to_infer=concept_repo.get_concept("$+({new number}:{number})"),
        function_concept=None,  # "none" case - no function concept
        value_concepts=[concept_repo.get_concept("{new number}")],
        flow_info={
            "flow_index": "1.2.1",
            "support": ["1.2.1.1"],
            "target": ["1.2"]
        }
        # No inference instance for this entry (optional)
    ),
    InferenceEntry(
        id=str(uuid.uuid4()),
        inference_sequence="imperative",
        concept_to_infer=concept_repo.get_concept("{new number}"),
        function_concept=concept_repo.get_concept("::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)"),
        value_concepts=[concept_repo.get_concept("{unit place digit}?"), concept_repo.get_concept("{number}")],
        flow_info={
            "flow_index": "1.2.1.1",
            "target": ["1.2.1"]
        },
        inference=Inference(
            sequence_name="imperative",
            concept_to_infer=concept_repo.get_concept("{new number}").concept,
            value_concepts=[concept_repo.get_concept("{unit place digit}?").concept, concept_repo.get_concept("{number}").concept],
            function_concept=concept_repo.get_concept("::(remove {2}?<$({unit place digit})%_> from {1}<$({number})%_>)").concept
        )
    ),
    InferenceEntry(
        id=str(uuid.uuid4()),
        inference_sequence="scheduling",
        concept_to_infer=concept_repo.get_concept("{index}*"),
        function_concept=concept_repo.get_concept("@after([{index} and {digit}]*)"),
        value_concepts=[concept_repo.get_concept("::(increment {1}<$({index})%_>)")],
        flow_info={
            "flow_index": "1.3",
            "support": ["1.3.1"],
            "target": ["1.1.1.1"]
        }
        # No inference instance for this entry (optional)
    ),
    InferenceEntry(
        id=str(uuid.uuid4()),
        inference_sequence="imperative",
        concept_to_infer=concept_repo.get_concept("::(increment {1}<$({index})%_>)"),
        function_concept=None,  # "none" case - no function concept
        value_concepts=[concept_repo.get_concept("{index}*")],
        flow_info={
            "flow_index": "1.3.1",
            "target": ["1.3"]
        }
        # No inference instance for this entry (optional)
    )
]

# Create the inference repository
inference_repo = InferenceRepo(inference_entries)

# Create the flow orchestrator
orchestrator = Orchestrator(inference_repo)

# Example usage of the flow orchestrator
def demonstrate_flow_execution():
    """Demonstrate the plan and execute workflow."""
    print("=== Orchestrator Demonstration ===")
    
    # 1. Create a plan
    print("\n1. Creating a new execution plan...")
    plan = orchestrator.plan()
    
    # 2. Show the plan
    orchestrator.show_plan(plan)
    
    # # 3. Execute the plan
    # print(f"\n2. Executing plan {plan.id}...")
    # orchestrator.execute_plan(plan)
    
    # # 4. Show summary
    # print(f"\n3. Final execution summary:")
    # orchestrator.print_summary()
    
    return orchestrator, plan

# Uncomment the line below to run the demonstration
# orchestrator, executed_plan = demonstrate_flow_execution()


if __name__ == "__main__":
    demonstrate_flow_execution()