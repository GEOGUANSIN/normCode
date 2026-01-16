# NormCode Repository Compatibility

When resuming an orchestration run from a checkpoint, the fundamental question is not just "are these files identical?", but **"Does the Checkpoint provide a valid Initial State for the New Repo?"**

This document defines compatibility in terms of **Data Sufficiency** and **State Validity**.

## The Core Principle: Data Sufficiency & Non-Interference

The Orchestrator's job is to execute a plan. A Checkpoint is compatible with a New Repo if it provides sufficient data to "kick start" execution *without* introducing stale logic that incorrectly steers the new plan.

### 1. Ground Concept Sufficiency
*   **Requirement:** Every concept in the New Repo ($R_{new}$) that serves as a **starting point** (a ground concept or a completed dependency for a pending step) must have data.
*   **Source:** This data usually comes from the Checkpoint ($S$).
*   **The Check:**
    *   Does $S$ contain a reference for every concept that $R_{new}$ expects to be already known?
    *   *Example:* If $R_{new}$ requires `{user age}` to calculate `{birth year}`, and `{user age}` is marked as an input, the Checkpoint *must* contain the reference for `{user age}`. If it's missing, the repo is incompatible (insufficient data).

### 2. State Validity (Blackboard & Workspace)
*   **Requirement:** The execution state in the Checkpoint must make sense to the Logic of the New Repo and **must not incorrectly override it**.
*   **The Problem:** Stale state can act as a "Trojan Horse," causing the new repo to skip steps or take wrong branches.
*   **The Check:**
    *   **Loops (`quantifying`):** If the Checkpoint says we are in iteration 5 of a loop over `{users}`, the New Repo must still have that loop structure. The **Workspace** in the Checkpoint contains loop counters and iteration variables (e.g., `i=5`, `current_user=UserE`). If $R_{new}$ deleted that loop or changed the iteration variable, the saved Workspace is effectively garbage, and we cannot resume.
    *   **Conditions (`judgement`):** This is critical. The Blackboard stores results of past conditions (e.g., `<is valid user> = True`).
        *   **Risk:** If $R_{new}$ uses `<is valid user>` in a `@if` step, it will read `True` from the Blackboard and potentially **skip execution** or **take a branch** immediately.
        *   **Validation:** We must ensure that the *logic* producing `<is valid user>` hasn't changed significantly. If the old repo set it to `True` based on logic A, but the new repo wants to calculate it using logic B, the saved `True` is **stale interference**. Resuming will bypass logic B entirely.

## Compatibility Levels (Revised)

### 1. Strict Identity (Ideal)
*   **Definition:** $R_{old}$ hash == $R_{new}$ hash.
*   **Verdict:** Guaranteed safe.

### 2. Sufficient State (Compatible)
*   **Definition:**
    *   $R_{new}$ is different from $R_{old}$.
    *   **BUT:** All "Ground Concepts" required by $R_{new}$ exist in the Checkpoint.
    *   **AND:** Any "Active" (in-progress) logic in the Checkpoint maps correctly to $R_{new}$.
    *   **AND:** Saved condition results in the Blackboard are semantically valid for the new repo (i.e., they don't accidentally trigger flow control paths that should be re-evaluated).
*   **Verdict:** Safe to resume.
    *   *Note:* Intermediate concepts that were completed in the Checkpoint but are no longer used in $R_{new}$ are simply ignored (orphaned data). This is fine.
    *   *Note:* New steps added to $R_{new}$ will simply start as `pending`.

### 3. Insufficient or Interfering State (Incompatible)
*   **Definition:**
    *   $R_{new}$ requires a Ground Concept that is missing from the Checkpoint.
    *   OR: The Checkpoint contains Workspace state (e.g., loop index) for a flow index that no longer exists or has changed type in $R_{new}$.
    *   OR: **Stale Interference**: The Checkpoint contains a completed condition (e.g., "True") for a concept that the New Repo treats as pending or redefined, causing the Orchestrator to incorrectly skip logic.
*   **Verdict:** Unsafe. Cannot resume because the state is either missing or actively harmful to the new plan.

## Validation Strategy

We validate by asking: **"Can we satisfy the dependencies of the pending items?"** AND **"Does the existing state corrupt the new logic?"**

1.  **Load Checkpoint:** Restore Blackboard (status, results) and References (data).
2.  **Identify Pending Frontier:** Find all items in $R_{new}$ that are ready to run or currently running.
3.  **Check Dependencies:** For each item on the frontier:
    *   Do its input concepts exist in the loaded References?
    *   Does its internal state (if resuming a loop) exist in the loaded Workspace?
4.  **Check for Interference:**
    *   Are there concepts marked `complete` in the Blackboard that $R_{new}$ expects to re-compute? (This requires checking if the *definition* of the concept or its inference step has changed).
5.  **Result:**
    *   If **Yes** (Dependencies Met AND No Interference): We can resume.
    *   If **No**: We halt with a "Data Insufficiency" or "State Conflict" error.

## Loading Modes: Controlling State Application

We can offer different modes for applying the Checkpoint state to the New Repo:

### 1. `OVERWRITE` (Strict Resume)
*   **Behavior:** The Checkpoint is the **absolute truth**.
*   **Rule:** If Checkpoint says Concept A is `complete`, we mark it `complete` in $R_{new}$ and use the saved value, ignoring any changes to A's definition or logic.
*   **Use Case:** Resuming an identical run or a minor extension where you trust the past execution fully.

### 2. `PATCH` (Smart Merge / Re-run Changed Logic)
*   **Behavior:** Apply Checkpoint state **unless** $R_{new}$ explicitly invalidates it.
*   **Rule:**
    *   If Concept A is `complete` in Checkpoint, BUT the definition of A or its inference step has changed in $R_{new}$ (hash mismatch), we **discard** the saved value and mark A as `pending`.
    *   This forces the Orchestrator to **re-run** the logic for A using the new definition.
*   **Use Case:** Fixing a bug in a specific step. "I fixed the prompt for Step 3. Keep the results of Steps 1 & 2, but re-run Step 3."

### 3. `FILL_GAPS` (Conservative)
*   **Behavior:** Only use Checkpoint data to fill **empty** spots in $R_{new}$.
*   **Rule:** If $R_{new}$ already has an initial value for Concept A (e.g., a new default), we ignore the Checkpoint value.
*   **Use Case:** Importing partial results into a largely fresh run.

## Handling Execution History

When resuming, what do we do with the old logs and execution records?

### Option A: Continuity (Same Run ID)
*   **Behavior:** Append to the existing execution history. Cycle count continues from where it left off.
*   **Use Case:** **Strict Identity** or minor **Safe Extensions**.
*   **Benefit:** Complete lineage of the process.

### Option B: Forking (New Run ID)
*   **Behavior:** Start a fresh execution history (Cycle 1), but initialized with the *State* of the old run.
*   **Use Case:** **Major Changes** or **Incompatible Repos** (forced resume).
*   **Benefit:** Clean logs for the new logic. Avoids confusion where `Step 1.1` meant "Logic A" in the past and "Logic B" now.
