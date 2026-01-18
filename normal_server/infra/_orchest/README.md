# NormCode Orchestration Module (`infra._orchest`)

This module provides the core orchestration engine for the NormCode framework. It is responsible for executing static plans (defined in repositories) dynamically, managing dependencies, state, control flow, and execution cycles.

## Overview

The orchestration module takes a set of **Concepts** (what exists) and **Inferences** (how to derive new concepts) and executes them in a dependency-aware manner. It handles:

- **Dependency Resolution**: Automatically determines which steps can run based on data availability and hierarchical structure.
- **State Management**: Tracks the status of every concept and execution step.
- **Control Flow**: Supports complex patterns like loops (`*every`), conditionals, timing gates (`@after`), and assignments (`$`).
- **Observability**: Detailed tracking and logging of the execution process.
- **Checkpointing & Persistence**: Saves execution state to a shared database, supporting both end-of-cycle and intra-cycle checkpointing. Multiple orchestrator runs can coexist in the same database via run_id isolation, enabling easy resumability and crash recovery.

## Core Components

### 1. Orchestrator (`_orchestrator.py`)
The main engine that drives the execution.
- **Cycle Loop**: Runs continuously until all tasks are complete or a deadlock is detected.
- **Readiness Checks**: Determines if an item is ready to run by checking its dependencies (supporting items, input concepts, function concepts).
- **Execution**: Delegates actual inference work to an `AgentFrame` (via `infra._agent`) and updates the system state based on the results.
- **Checkpointing**: Saves state at the end of each cycle (and optionally every N inferences within a cycle) if a database path is provided. Each orchestrator instance has a unique `run_id` for isolation.

### 2. Blackboard (`_blackboard.py`)
The shared memory / state store.
- **Concept Status**: Tracks if concepts are `empty` or `complete`.
- **Item Status**: Tracks if execution steps are `pending`, `in_progress`, `completed`, or `failed`.
- **Results**: Stores execution results and completion details (e.g., `skipped`, `condition_not_met`).

### 3. Persistence Layer
Components for state persistence and recovery.
- **OrchestratorDB (`_db.py`)**: A SQLite wrapper handling `executions`, `logs`, and `checkpoints` tables.
    - Stores a record of every inference execution attempt, isolated by `run_id`.
    - Captures full logs emitted during execution (via `infra._loggers.ExecutionLogHandler`).
    - Supports multiple orchestrator runs in the same database via `run_id` isolation.
    - Provides methods to list runs and query checkpoints by cycle and inference count.
- **CheckpointManager (`_checkpoint.py`)**: Manages the serialization and restoration of the full system state.
    - Saves the Blackboard, Tracker, Workspace, and completed Concept References as JSON blobs.
    - Supports both end-of-cycle and intra-cycle checkpointing (via `inference_count`).
    - Can load checkpoints by cycle number and inference count for precise resumption.
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

## Checkpointing Features

The orchestration module supports advanced checkpointing capabilities:

### Run ID Isolation
- Each orchestrator instance has a unique `run_id` (UUID by default, or user-specified).
- Multiple runs can coexist in the same database file, isolated by `run_id`.
- Useful for running experiments, A/B testing, or managing multiple execution sessions.

### Checkpoint Granularity
- **End-of-Cycle Checkpointing**: Default behavior - saves state at the end of each cycle.
- **Intra-Cycle Checkpointing**: Optional `checkpoint_frequency` parameter saves state every N inferences within a cycle.
  - Example: `checkpoint_frequency=5` saves at inferences 5, 10, 15, etc. within each cycle.
  - Useful for long-running cycles or when you need fine-grained recovery points.

### Checkpoint Identification
- Checkpoints are identified by `(run_id, cycle, inference_count)`.
- `inference_count=0` marks end-of-cycle checkpoints.
- Allows precise resumption from any saved state.

### Checkpoint Management
- `Orchestrator.list_available_checkpoints()`: List all checkpoints for a run.
- `OrchestratorDB.list_runs()`: List all runs in a database.
- `load_checkpoint()`: Resume from latest or specific checkpoint by cycle/inference_count.

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
    db_path="orchestration.db",  # Enables checkpointing
    checkpoint_frequency=5,     # Optional: checkpoint every 5 inferences (None = only at end of cycle)
    run_id="my-run"              # Optional: specify run_id (default: generates UUID)
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
        max_cycles=100,
        run_id="my-run"          # Optional: specify which run to resume
    )
    orchestrator.run()

# Resume from a specific checkpoint (by cycle and inference count)
orchestrator = Orchestrator.load_checkpoint(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    db_path="orchestration.db",
    body=body,
    max_cycles=100,
    run_id="my-run",
    cycle=3,                     # Load checkpoint from cycle 3
    inference_count=10           # Load checkpoint at inference 10 within that cycle
)

# List available runs and checkpoints
runs = OrchestratorDB("orchestration.db").list_runs()
checkpoints = Orchestrator.list_available_checkpoints("orchestration.db", run_id="my-run")
```

## Execution Flow

1.  **Initialization**: The Orchestrator builds a `Waitlist` from the `InferenceRepo` and initializes the `Blackboard` with all concepts. Ground concepts (inputs) are marked as `complete`. If resuming, state is reconciled from the DB.
2.  **Cycle Loop**:
    - The Orchestrator scans the `Waitlist` for items that are `pending`.
    - Checks `_is_ready(item)`: Are all dependencies (supporting items, input values) met?
    - If ready, `_execute_item(item)` runs the inference via an `AgentFrame`.
    - **Log Capture**: A specialized `ExecutionLogHandler` captures all logs during inference and saves them to the DB linked to the execution record (includes run_id context).
    - The `Blackboard` is updated with the new state (completed items, new concept references).
    - **Checkpoint**: 
      - If `checkpoint_frequency` is set, saves state every N inferences within the cycle.
      - Always saves state at the end of each cycle (with `inference_count=0` as marker).
      - Each checkpoint is stored with `(run_id, cycle, inference_count)` as the composite key.
3.  **Completion**: The loop ends when all items are processed. Final results are returned.
