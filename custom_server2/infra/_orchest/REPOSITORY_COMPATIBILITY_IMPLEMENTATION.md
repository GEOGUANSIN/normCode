# Repository Compatibility & Smart Resume Implementation

This document summarizes the implementation of repository compatibility checks and smart resume capabilities for the NormCode orchestration engine. This implementation addresses the requirements defined in `infra/_orchest/REPO_COMPATIBILITY.md`.

## Background

### The Problem

When resuming an orchestration run from a checkpoint, the fundamental question is: **"Does the Checkpoint provide a valid Initial State for the New Repo?"** 

The previous implementation only checked if files were identical. However, in practice, repositories evolve:
- Code logic changes (bug fixes, prompt improvements)
- New steps are added or removed
- Data dependencies change

Simply overwriting state from a checkpoint can introduce **stale interference** - where old logic results incorrectly steer new execution, causing steps to be skipped or wrong branches to be taken.

### Key Concepts

1. **Data Sufficiency**: Every ground concept (input) required by the new repo must have data available (either in repo or checkpoint).

2. **State Validity**: The execution state (Blackboard, Workspace) must make sense for the new repo's logic:
   - Loop counters must map to valid flow indices
   - Condition results must not corrupt new logic paths

3. **Stale Interference**: When logic has changed, using old checkpoint values can bypass new logic entirely.

## Implementation Overview

The implementation adds three major capabilities:

1. **Logic Signatures**: Detect when concept or inference definitions have changed
2. **Smart Reconciliation**: Three loading modes (PATCH, OVERWRITE, FILL_GAPS) for controlling state application
3. **Execution History Forking**: Option to start a fresh run history while preserving state

## Changes Made

### 1. Logic Signatures (`infra/_orchest/_repo.py`)

Added `get_signature()` methods to detect changes in logic definitions:

- **`ConceptEntry.get_signature()`**: Hashes concept definition fields:
  - `concept_name`, `type`, `context`, `axis_name`, `natural_name`
  - `is_ground_concept`, `is_invariant`
  
- **`InferenceEntry.get_signature()`**: Hashes inference definition fields:
  - `inference_sequence`, `concept_to_infer`, `function_concept`
  - `value_concepts`, `context_concepts`, `flow_index`
  - `working_interpretation` (parsed syntax)

These signatures enable comparison between saved checkpoint logic and current repo logic.

### 2. Enhanced Checkpointing (`infra/_orchest/_checkpoint.py`)

**Modified `CheckpointManager.save_state()`:**
- Now saves signature metadata for all completed concepts and items
- Structure:
  ```python
  {
      "signatures": {
          "concept_signatures": {concept_name: signature_hash, ...},
          "item_signatures": {flow_index: signature_hash, ...}
      },
      ...
  }
  ```

**Enhanced `CheckpointManager.reconcile_state()`:**
- Added `mode` parameter: `"PATCH"`, `"OVERWRITE"`, or `"FILL_GAPS"`
- **PATCH Mode** (default): Smart merge
  - Compares saved signatures vs current signatures
  - If mismatch: Discard checkpoint value, mark as `pending` (force re-run)
  - If match: Keep checkpoint value
  - Logs which concepts/items were discarded vs kept
  
- **OVERWRITE Mode**: Trust checkpoint completely
  - Applies all checkpoint values regardless of logic changes
  
- **FILL_GAPS Mode**: Conservative fill
  - Only applies checkpoint values for concepts that are `empty` in new repo
  - Prefers new repo defaults if they exist

### 3. Compatibility Validation (`infra/_orchest/_orchestrator.py`)

**Added `_validate_repo_compatibility()` method:**
- Checks **Data Sufficiency**: All ground concepts must have data
- Checks **Workspace Validity**: Loop counters must map to valid flow indices  
- Checks **Stale Interference**: Pre-detects concepts with changed logic
- Returns:
  ```python
  {
      'compatible': bool,
      'warnings': List[str],
      'errors': List[str]
  }
  ```

**Enhanced `Orchestrator.load_checkpoint()`:**
- Added `mode` parameter (default: `"PATCH"`)
- Added `validate_compatibility` parameter (default: `True`)
- Added `new_run_id` parameter for **Execution History Forking**

### 4. Execution History Forking (`infra/_orchest/_orchestrator.py`)

**New `new_run_id` parameter:**
- Enables **Option B: Forking** from `REPO_COMPATIBILITY.md`
- **Option A (Continuity)**: `load_checkpoint(..., run_id="A")`
  - Loads state from Run A
  - Continues writing to Run A
  - Cycle count continues from checkpoint
  
- **Option B (Forking)**: `load_checkpoint(..., run_id="A", new_run_id="B")`
  - Loads state from Run A
  - Starts fresh history for Run B
  - Resets execution counters and cycle count to 0
  - Preserves completed concept state (Blackboard)

**Added `ProcessTracker.reset_counters()` method:**
- Resets all execution statistics when forking
- Clears `completion_order`, execution counts, etc.

## Usage Examples

### Basic Resume with PATCH Mode (Default)

```python
from infra._orchest import Orchestrator, ConceptRepo, InferenceRepo

# Load repositories (potentially modified from checkpoint)
concept_repo = ConceptRepo.from_json_list(concept_data)
inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)

# Resume with smart merge
orchestrator = Orchestrator.load_checkpoint(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    db_path="orchestration.db",
    run_id="original-run-123",
    mode="PATCH",  # Default - discards stale state, keeps valid state
    validate_compatibility=True  # Default - checks data sufficiency
)

orchestrator.run()
```

**What happens:**
- Loads checkpoint from `"original-run-123"`
- Compares signatures: If a concept's logic changed, its checkpoint value is discarded
- Continues writing to `"original-run-123"` (Option A: Continuity)

### Resume with Forking (Option B)

```python
import uuid

# Resume from old run but start a new run history
orchestrator = Orchestrator.load_checkpoint(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    db_path="orchestration.db",
    run_id="original-run-123",  # Source run
    new_run_id=f"fork-{uuid.uuid4()}",  # New run ID
    mode="PATCH"
)

orchestrator.run()
```

**What happens:**
- Loads state from `"original-run-123"`
- Initializes new orchestrator with `new_run_id`
- Resets cycle count to 0, execution counters to 0
- Preserves completed concept state (data)
- Starts fresh execution history for the new run

### Resume with OVERWRITE Mode

```python
# Trust checkpoint completely (no signature checking)
orchestrator = Orchestrator.load_checkpoint(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    db_path="orchestration.db",
    run_id="original-run-123",
    mode="OVERWRITE"  # Ignores any logic changes
)
```

### Resume with FILL_GAPS Mode

```python
# Only fill missing values, prefer new repo defaults
orchestrator = Orchestrator.load_checkpoint(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    db_path="orchestration.db",
    run_id="original-run-123",
    mode="FILL_GAPS"
)
```

## When to Use Each Mode

| Mode | Use Case | Behavior |
|------|----------|----------|
| **PATCH** | Bug fixes, prompt improvements | Discards stale state, keeps valid state. Recommended default. |
| **OVERWRITE** | Identical repos, minor extensions | Trusts checkpoint 100%. Use with caution if repo changed. |
| **FILL_GAPS** | Importing partial results | Only fills empty concepts. Prefers new repo defaults. |

| History Option | Use Case | Command |
|----------------|----------|---------|
| **Continuity (A)** | Minor changes, want complete lineage | `load_checkpoint(..., run_id="A")` |
| **Forking (B)** | Major changes, want clean logs | `load_checkpoint(..., run_id="A", new_run_id="B")` |

## Validation Behavior

When `validate_compatibility=True` (default), the system:

1. **Checks Data Sufficiency**:
   - Errors if any ground concept is missing data
   - Logs warnings for stale concepts

2. **Logs Compatibility Results**:
   ```
   WARNING: Repository compatibility validation found 2 warning(s):
     - Concept '{digit sum}' has changed logic (signature mismatch). Will be re-run in PATCH mode.
     - Concept '{remainder}' has changed logic (signature mismatch). Will be re-run in PATCH mode.
   ```

3. **Proceeds with Reconciliation**:
   - Even if incompatible, reconciliation proceeds (with warnings)
   - Execution may fail if dependencies are truly missing

## Technical Details

### Signature Generation

Signatures use SHA-256 hash of JSON-serialized definition fields:
- Deterministic: Same definition → same signature
- Sensitive: Any change in logic → different signature
- Content-based: Based on definition structure, not exact text

### Checkpoint Structure

Enhanced checkpoint now includes:
```python
{
    "blackboard": {...},
    "tracker": {...},
    "workspace": {...},
    "completed_concepts": {...},
    "signatures": {
        "concept_signatures": {
            "{concept_name}": "abc123...",
            ...
        },
        "item_signatures": {
            "1.1.2": "def456...",
            ...
        }
    }
}
```

### Forking Details

When forking (`new_run_id` is provided):
1. State is loaded from source `run_id`
2. Orchestrator is initialized with `new_run_id`
3. Tracker counters are reset:
   - `cycle_count = 0`
   - `total_executions = 0`
   - `completion_order = []`
4. Completed concepts (Blackboard) are preserved
5. New execution history starts at Cycle 1

## Files Modified

1. **`infra/_orchest/_repo.py`**
   - Added `ConceptEntry.get_signature()`
   - Added `InferenceEntry.get_signature()`

2. **`infra/_orchest/_checkpoint.py`**
   - Modified `save_state()` to include signatures
   - Enhanced `reconcile_state()` with mode support

3. **`infra/_orchest/_orchestrator.py`**
   - Added `_validate_repo_compatibility()` method
   - Enhanced `load_checkpoint()` with `mode`, `validate_compatibility`, `new_run_id`

4. **`infra/_orchest/_tracker.py`**
   - Added `reset_counters()` method for forking support

## Related Documentation

- **Design Document**: `infra/_orchest/REPO_COMPATIBILITY.md`
- **Orchestration Guide**: `infra/_orchest/README.md`
- **NormCode Execution**: `infra/_orchest/NORMCODE_ORCHESTRATION.md`

## Example Scenarios

### Scenario 1: Fixing a Bug in One Step

**Situation**: You ran an orchestration and found a bug in the prompt for `{digit sum}`. You fixed the prompt but want to keep all other results.

**Solution**:
```python
# Fix the prompt in your repo definition, then:
orchestrator = Orchestrator.load_checkpoint(
    concept_repo=concept_repo,  # With fixed prompt
    inference_repo=inference_repo,
    db_path="orchestration.db",
    run_id="original-run",
    mode="PATCH"  # Will re-run {digit sum} but keep everything else
)
```

**Result**: `{digit sum}` signature mismatch detected → discarded → re-run with new prompt. All other concepts kept.

### Scenario 2: Major Repository Restructure

**Situation**: You've significantly restructured the repository (changed flow indices, added new steps). You want to resume but with clean logs.

**Solution**:
```python
orchestrator = Orchestrator.load_checkpoint(
    concept_repo=concept_repo,  # New structure
    inference_repo=inference_repo,  # New structure
    db_path="orchestration.db",
    run_id="original-run",
    new_run_id="restructured-run-v2",  # Fork to new run
    mode="PATCH"
)
```

**Result**: State transferred from old run, but execution history starts fresh. Cycle 1 of new run begins.

### Scenario 3: Importing Partial Results

**Situation**: You want to use some results from a previous run but mostly start fresh with new defaults.

**Solution**:
```python
orchestrator = Orchestrator.load_checkpoint(
    concept_repo=concept_repo,  # Has new defaults
    inference_repo=inference_repo,
    db_path="orchestration.db",
    run_id="partial-run",
    mode="FILL_GAPS"  # Only fills empty concepts
)
```

**Result**: New repo defaults are preserved. Only empty concepts get checkpoint values.

## Notes for Future Conversations

This implementation provides:
- **Safe resumption** even when repository logic changes
- **Flexible control** over how checkpoint state is applied
- **Clean history management** via forking
- **Comprehensive validation** before resuming

The default `PATCH` mode is recommended for most use cases as it provides the safest "smart resume" behavior - keeping valid state while discarding stale logic.

