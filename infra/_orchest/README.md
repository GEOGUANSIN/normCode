# NormCode Orchestration Module (`infra._orchest`)

This module provides the core orchestration engine for the NormCode framework. It is responsible for executing static plans (defined in repositories) dynamically, managing dependencies, state, control flow, and execution cycles.

## Overview

The orchestration module takes a set of **Concepts** (what exists) and **Inferences** (how to derive new concepts) and executes them in a dependency-aware manner. It handles:

- **Dependency Resolution**: Automatically determines which steps can run based on data availability and hierarchical structure.
- **State Management**: Tracks the status of every concept and execution step.
- **Control Flow**: Supports complex patterns like loops (`*every`), conditionals, timing gates (`@after`), and assignments (`$`).
- **Observability**: Detailed tracking and logging of the execution process.
- **Checkpointing & Persistence**: Saves execution state per cycle to a shared database, allowing for resumability and crash recovery.

## Core Components

### 1. Orchestrator (`_orchestrator.py`)
The main engine that drives the execution.
- **Cycle Loop**: Runs continuously until all tasks are complete or a deadlock is detected.
- **Readiness Checks**: Determines if an item is ready to run by checking its dependencies (supporting items, input concepts, function concepts).
- **Execution**: Delegates actual inference work to an `AgentFrame` (via `infra._agent`) and updates the system state based on the results.
- **Checkpointing**: Triggers a state save at the end of each cycle if a database path is provided.

### 2. Blackboard (`_blackboard.py`)
The shared memory / state store.
- **Concept Status**: Tracks if concepts are `empty` or `complete`.
- **Item Status**: Tracks if execution steps are `pending`, `in_progress`, `completed`, or `failed`.
- **Results**: Stores execution results and completion details (e.g., `skipped`, `condition_not_met`).

### 3. Persistence Layer
Components for state persistence and recovery.
- **OrchestratorDB (`_db.py`)**: A SQLite wrapper handling `executions`, `logs`, and `checkpoints` tables.
    - Stores a record of every inference execution attempt.
    - Captures full logs emitted during execution (via `infra._loggers.ExecutionLogHandler`).
- **CheckpointManager (`_checkpoint.py`)**: Manages the serialization and restoration of the full system state.
    - Saves the Blackboard, Tracker, Workspace, and completed Concept References as JSON blobs.
    - Supports `export_comprehensive_state()` for debugging and analysis.

### 4. Repositories (`_repo.py`)
Data access layer for the execution plan.
- **ConceptRepo**: Stores `ConceptEntry` objects (definitions of variables, files, prompts).
- **InferenceRepo**: Stores `InferenceEntry` objects (definitions of steps/actions).
- **Factories**: Can load repositories from JSON definitions.

### 5. Waitlist (`_waitlist.py`)
Manages the execution queue.
- **WaitlistItem**: Wraps an `InferenceEntry` for tracking.
- **Ordering**: Sorts items by `flow_index` (e.g., `1`, `1.1`, `1.2`) to establish a default bottom-up execution order.
- **Dependency Helpers**: Identifies supporting items (children) and dependent items (consumers).

### 6. Process Tracker (`_tracker.py`)
Observability component.
- Records every execution cycle, attempt, success, failure, and retry.
- Generates a comprehensive summary log at the end of execution.
- Integrates with `OrchestratorDB` to persist execution history.

### 7. Parsers (`_parser.py`)
Utilities for parsing NormCode expressions used in the repositories.
- Handles syntax for Grouping (`&`), Quantifying (`*every`), Assigning (`$`), and Timing (`@after`).
- **⚠️ Note**: This parser is still under development and is only a temporary version. The parsing logic may change in future iterations as the NormCode syntax evolves.

## Usage Example

### Basic Execution

```python
from infra._orchest import Orchestrator, ConceptRepo, InferenceRepo
from infra._agent._body import Body

# 1. Load Repositories (usually from JSON)
concept_repo = ConceptRepo.from_json_list(concept_data)
inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)

# 2. Initialize Body (LLM connection)
body = Body(llm_name="gpt-4o", base_dir="./")

# 3. Initialize Orchestrator with Checkpointing
orchestrator = Orchestrator(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    body=body,
    max_cycles=100,
    db_path="orchestration.db"  # Enables checkpointing
)
 
# 4. Run
final_concepts = orchestrator.run()

# 5. Process Results
for concept in final_concepts:
    print(f"Result: {concept.concept_name} -> {concept.concept.reference}")
```

### Resuming from Checkpoint

```python
# Resume execution from the last saved state in the database
if os.path.exists("orchestration.db"):
    orchestrator = Orchestrator.load_checkpoint(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        db_path="orchestration.db",
        body=body,
        max_cycles=100
    )
    orchestrator.run()
```

## Execution Flow

1.  **Initialization**: The Orchestrator builds a `Waitlist` from the `InferenceRepo` and initializes the `Blackboard` with all concepts. Ground concepts (inputs) are marked as `complete`. If resuming, state is reconciled from the DB.
2.  **Cycle Loop**:
    - The Orchestrator scans the `Waitlist` for items that are `pending`.
    - Checks `_is_ready(item)`: Are all dependencies (supporting items, input values) met?
    - If ready, `_execute_item(item)` runs the inference via an `AgentFrame`.
    - **Log Capture**: A specialized `ExecutionLogHandler` captures all logs during inference and saves them to the DB linked to the execution record.
    - The `Blackboard` is updated with the new state (completed items, new concept references).
    - **Checkpoint**: At the end of the cycle, `CheckpointManager` saves the full state to the DB.
3.  **Completion**: The loop ends when all items are processed. Final results are returned.
