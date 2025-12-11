# NormCode Guide - The Orchestrator

The **Orchestrator** is the central engine of the NormCode system. While NormCode scripts define *what* should happen (the plan) and Agents define *how* to do it (the capabilities), the Orchestrator defines *when* it happens. It manages the execution flow, dependency resolution, state tracking, and persistence of the entire inference plan.

## 1. Core Architecture

The Orchestrator operates on a dependency-driven, bottom-up execution model. An inference is executed only when its required inputs (value concepts) and logical dependencies are ready.

### 1.1. Key Components

*   **`Orchestrator`**: The main class that runs the execution loop.
*   **`Waitlist`**: A prioritized queue of all `InferenceEntry` items, sorted hierarchically by their `flow_index` (e.g., `1.1`, `1.1.2`). This static list defines the structural order of the plan.
*   **`Blackboard`**: The dynamic state container. It tracks the real-time status (`pending`, `in_progress`, `completed`, `skipped`) of every concept and inference. It is the "single source of truth" for readiness checks.
*   **`ProcessTracker`**: A logging system that records the history of every execution cycle, including success/failure rates and detailed logs.
*   **`Repositories`**:
    *   `ConceptRepo`: Stores the definitions and references (data) of all concepts.
    *   `InferenceRepo`: Stores the definitions of all inferences.

## 2. The Execution Logic

The Orchestrator runs in **Cycles**. In each cycle, it iterates through the `Waitlist` to find and execute "ready" inferences.

### 2.1. Readiness Criteria
An inference is considered **Ready** to run only if:
1.  **Dependencies are Met**: All "supporting items" (child inferences in the indentation tree) are `completed`.
2.  **Functional Concept is Ready**: The concept defining the operation (e.g., the specific imperative command) is `complete`.
3.  **Value Concepts are Ready**: All input concepts (data) required for the operation are `complete`.
    *   *Exception*: For `assigning` inferences with multiple candidate sources, only *one* valid source needs to be ready.

### 2.2. The Execution Cycle
1.  **Check**: The Orchestrator scans the `Waitlist` for `pending` items that satisfy the readiness criteria.
2.  **Execute**: It constructs an `AgentFrame` for the item and triggers the inference execution (e.g., calling an LLM or tool).
3.  **Update**:
    *   **Success**: The item is marked `completed`. The result (reference) is updated in the `ConceptRepo`.
    *   **Failure**: The item is marked for retry (or failed if critical).
    *   **Skip**: If a Timing inference (e.g., `@if`) determines a branch should be skipped, the Orchestrator **propagates the skip state** to all dependent children, marking them as `completed` (with detail `skipped`) so the plan can proceed without them.

## 3. Advanced Orchestration Features

### 3.1. Loop Management (Quantifying)
The Orchestrator has specialized logic for handling loops (`*every`).
*   **Workspace**: It maintains a `workspace` to track the iteration state of each quantifier.
*   **Reset & Re-run**: When a loop finishes one iteration but hasn't processed all items, the Orchestrator **resets the status** of all its child inferences (supporting items) back to `pending`. This allows the same logical structure to be re-executed for the next item in the collection.
*   **Invariant Concepts**: Concepts marked as "invariant" are *not* reset, preserving their value across iterations (useful for accumulating results or constants).

### 3.2. Persistence and Checkpointing
The Orchestrator includes a robust **Checkpointing System** backed by a SQLite database (`OrchestratorDB`).

*   **Run IDs**: Every execution is associated with a unique `run_id`. You can resume a past run or "fork" it into a new run.
*   **Snapshots**: It saves the full state (Blackboard, Workspace, References) at the end of every cycle (or more frequently if configured).
*   **Resuming & Forking**:
    *   **Resume**: Continue a run from where it left off.
    *   **Fork**: Load a past state but start a new history (new `run_id`). Useful for "branching" experiments or retrying from a specific point.

### 3.3. Compatibility & Patching
When loading a checkpoint, the codebase (definitions in Repos) might have changed since the run was saved. The Orchestrator handles this via **Reconciliation Modes**:

*   **`PATCH` Mode (Default)**: A "Smart Merge". It loads the saved state but validates it against the current Repos.
    *   If a concept's definition (logic signature) has changed, its saved state is discarded (set to `pending`) so it re-runs with the new logic.
    *   Valid states are kept, saving time.
*   **`OVERWRITE`**: Trusts the checkpoint entirely (legacy behavior).
*   **`FILL_GAPS`**: Only populates missing data, preferring current Repo defaults.

The system also validates the **Environment Compatibility** (e.g., checking if the LLM model or AgentFrame settings match the saved run) and warns of discrepancies.

## 4. Usage

### 4.1. Basic Execution
```python
orchestrator = Orchestrator(concept_repo, inference_repo)
final_concepts = orchestrator.run()
```

### 4.2. Loading from Checkpoint (Patch Mode)
```python
# Resumes the latest run, re-running any modified logic
orchestrator = Orchestrator.load_checkpoint(
    concept_repo, 
    inference_repo, 
    db_path="orchestration.db",
    mode="PATCH"
)
orchestrator.run()
```

### 4.3. Async Support
The Orchestrator fully supports asynchronous execution for non-blocking operations in web or UI contexts:
```python
await orchestrator.run_async()
```

## 5. Tools for Running the Orchestrator

While you can write custom scripts, NormCode provides two primary tools for running and managing orchestrations.

### 5.1. Command Line Interface (CLI)

The `cli_orchestrator.py` tool provides a robust way to run, resume, and manage orchestrations from the terminal.

**Common Commands:**

*   **Start a Fresh Run**:
    ```bash
    python cli_orchestrator.py run --concepts concepts.json --inferences inferences.json --inputs inputs.json
    ```

*   **Resume a Run**:
    ```bash
    # Resumes the latest run in 'PATCH' mode (smart merge)
    python cli_orchestrator.py resume --concepts concepts.json --inferences inferences.json

    # Resume a specific run ID
    python cli_orchestrator.py resume --concepts concepts.json --inferences inferences.json --run-id <UUID>
    ```

*   **List Runs**:
    ```bash
    python cli_orchestrator.py list-runs
    ```

*   **Fork a Run**:
    Creates a new run history starting from an old checkpoint, often used with updated repositories.
    ```bash
    python cli_orchestrator.py fork --concepts new_concepts.json --inferences new_inferences.json --from-run <OLD_UUID>
    ```

### 5.2. Streamlit Application

The `streamlit_app` provides a visual interface for the Orchestrator. It is ideal for monitoring progress, debugging, and inspecting the state of concepts in real-time.

*   **Visualizes the Plan**: Shows the hierarchy of inferences as a tree.
*   **Real-time Status**: Updates the status (pending/running/done) of each step live.
*   **Inspection**: Click on any concept to view its current value/reference.
*   **Controls**: Buttons to Start, Pause, Resume, and Reset runs.

**To Launch:**
```bash
streamlit run streamlit_app/app.py
```
