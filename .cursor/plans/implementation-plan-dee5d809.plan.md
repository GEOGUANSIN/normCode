<!-- dee5d809-c0e1-4c3a-b849-8008058e34cc 8be56005-4a50-484e-89b8-1df8e59f8540 -->
# Implementation Plan - Repository Compatibility & Smart Resume

This plan implements the "Data Sufficiency" and "State Validity" checks defined in `REPO_COMPATIBILITY.md`, introducing a smart `PATCH` loading mode that prevents stale state from corrupting new execution plans.

## 1. Logic Signatures (`infra/_orchest/_repo.py`)

To detect changes in logic, we need deterministic signatures for Concepts and Inferences.

-   Add `get_signature()` to `ConceptEntry`: Hashes name, type, context, and ground status.
-   Add `get_signature()` to `InferenceEntry`: Hashes sequence type, input dependencies (`value_concepts`, `function_concept`), and `working_interpretation` (parsed syntax).

## 2. Enhanced Checkpointing (`infra/_orchest/_checkpoint.py`)

Checkpoints must store "what logic created this state" to allow comparison later.

-   **Save**: Update `save_state` to include a `signatures` block:
    -   `concept_signatures`: Map of `{concept_name: signature_hash}` for all completed concepts.
    -   `item_signatures`: Map of `{flow_index: signature_hash}` for all completed items.
-   **Load**: Update `reconcile_state` to accept a `mode` parameter (`PATCH` [default], `OVERWRITE`, `FILL_GAPS`).

## 3. Compatibility Validation Logic (`infra/_orchest/_orchestrator.py`)

Implement the validation strategy to ensure safety before loading.

-   **Data Sufficiency Check**: Ensure all `is_ground_concept=True` items in the new repo have data (either in repo or checkpoint).
-   **Stale Interference Check**: In `PATCH` mode, compare `saved_signature` vs `current_signature`.
    -   If Mismatch: Discard checkpoint value (mark as `pending` to re-run).
    -   If Match: Keep checkpoint value.
-   **Workspace Validity**: Check if loop counters in the checkpoint match valid flow indices in the new repo.

## 4. Integration

-   Update `Orchestrator.load_checkpoint` to expose the `mode` argument.
-   Connect the validation logic to the loading flow.

## Implementation Steps

1.  **Signatures**: Update `_repo.py` with hashing logic.
2.  **Checkpoint Structure**: Update `_checkpoint.py` to save/load signatures.
3.  **Smart Reconciliation**: Implement the `PATCH/OVERWRITE/FILL_GAPS` logic in `_checkpoint.py`.
4.  **Orchestrator Update**: Wire everything into `_orchestrator.py`.

### To-dos

- [ ] Add get_signature() methods to ConceptEntry and InferenceEntry in _repo.py
- [ ] Update CheckpointManager.save_state to include signature metadata
- [ ] Implement reconcile_state logic for PATCH, OVERWRITE, FILL_GAPS modes
- [ ] Implement validation logic and update Orchestrator.load_checkpoint