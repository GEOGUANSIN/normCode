<!-- 8f304b7a-f8b8-4ced-891d-7d71c38fc0f9 950acf22-4969-40db-8865-f9fd936a0e2b -->
# Implementation Plan - Orchestration Checkpointing System

This plan introduces a checkpointing mechanism to persist orchestration state per cycle and enable restoration into new orchestration instances with plan compatibility checks. It also includes capturing and persisting logs for each inference in a shared database.

## 1. Shared Database Implementation (`infra/_orchest/_db.py`)

We will introduce a lightweight, shared database module using SQLite to be used by both `ProcessTracker` and `CheckpointManager`.

### Key Responsibilities:

- **Unified Storage**: Store execution history, logs, and cycle states in a single persistent location (e.g., `orchestration.db` in the checkpoint directory).
- **Tables**:
- `executions`: Stores metadata for each inference attempt (id, flow_index, cycle, status, concept_inferred, timestamp).
- `logs`: Stores detailed logs linked to specific execution IDs.
- `checkpoints`: Stores snapshots of the `Blackboard`, `ConceptRepo` (completed references), and `Workspace` state per cycle (JSON blobs).

## 2. Update ProcessTracker (`infra/_orchest/_tracker.py`)

- **Use Shared DB**: Instead of holding `execution_history` in memory lists, `ProcessTracker` will write directly to the shared database.
- **Methods**:
- `add_execution_record(...)`: Insert a row into `executions` and return the row ID.
- `capture_inference_log(execution_id, log_content)`: Insert detailed logs into `logs` linked to the execution ID.
- `get_history()`: Query the DB for reporting/summary.
- `load_from_db()`: Initialize internal counters (success/fail counts) by querying the DB upon restart.

## 3. Update Checkpoint Manager (`infra/_orchest/_checkpoint.py`)

- **Use Shared DB**:
- **Save**: Serialize the high-level `Blackboard`, `ConceptRepo` references, and `Workspace` state and store it in the `checkpoints` table as a JSON blob, keyed by cycle number.
- **Load (Reconcile)**:
- Query the `checkpoints` table for the latest cycle.
- Deserialize the JSON blob to rehydrate the `Blackboard`, `ConceptRepo`, and `Workspace`.
- The `ProcessTracker`'s history is already in the DB, so `reconcile` just needs to ensure counters are synced.

## 4. Integrate with Orchestrator (`infra/_orchest/_orchestrator.py`)

- **Initialization**: Initialize the `OrchestratorDB` and pass it to both `ProcessTracker` and `CheckpointManager`.
- **Workflow**:
- `ProcessTracker` writes execution records and logs incrementally during execution.
- `CheckpointManager` writes the state snapshot at the end of each cycle.
- `load_checkpoint`: New method to initialize the system from an existing DB file.

## 5. Expose Module (`infra/_orchest/__init__.py`)

- Export `CheckpointManager` and `OrchestratorDB` in `__init__.py`.

## 6. Verification (Mental Check)

- **Consistency**: Logs are written immediately, preserving data even if a crash occurs before the cycle checkpoint.
- **Efficiency**: Heavy logs are stored in a separate table and only loaded when needed, keeping the main checkpoint JSON lightweight.
- **Continuity**: Resuming involves opening the SQLite file; all history is instantly available.

## Implementation Steps

1. Create `infra/_orchest/_db.py` (Shared Database implementation).
2. Modify `infra/_orchest/_tracker.py` to use the shared database.
3. Create `infra/_orchest/_checkpoint.py` (modified to use shared DB).
4. Modify `infra/_orchest/_orchestrator.py`.
5. Update `infra/_orchest/__init__.py`.