# Repository Forking Guide - Streamlit App

## What is Forking?

**Forking** is a powerful feature that allows you to:
1. Load completed concepts from one orchestration run
2. Upload a **different** repository
3. Execute the new repository using the loaded concepts
4. Start a fresh execution history

This enables **repository chaining** - connecting multiple repositories together in a pipeline.

## Why Use Forking?

### Use Cases

✅ **Multi-stage pipelines**: Process data through multiple repositories  
✅ **Repository chaining**: Output of one repo → Input of another  
✅ **Reuse expensive computations**: Don't re-run costly operations  
✅ **Testing variations**: Try different post-processing on same data  
✅ **Modular workflows**: Break complex tasks into smaller repositories  

### Example: Addition → Combination

**Stage 1 (Addition):**
- Input: Two numbers `123` and `98`
- Repository: `addition_concepts.json`, `addition_inferences.json`
- Output: `{new number pair}` with digit-by-digit addition results
- Result: `[['2', '2', '1'], ['1']]` (221 in reverse, with carry)

**Stage 2 (Combination):**
- Input: Load `{new number pair}` from Stage 1 checkpoint
- Repository: `combination_concepts.json`, `combination_inferences.json`
- Output: `{sum}` as a single combined number
- Result: `221`

## How to Fork in the Streamlit App

### Step-by-Step Guide

#### 1. Run the First Repository

1. Upload your first repository files (e.g., addition)
   - `addition_concepts.json`
   - `addition_inferences.json`
   - `addition_inputs.json`

2. Configure settings:
   - LLM Model: Choose your model
   - Max Cycles: Set appropriate limit
   - Execution Mode: **Fresh Run**

3. Click "▶️ Start Execution"

4. **Note the Run ID** displayed after execution
   - Example: `run-abc123...`

#### 2. Fork to Second Repository

1. Upload your second repository files (e.g., combination)
   - `combination_concepts.json`
   - `combination_inferences.json`
   - **No inputs.json** (data comes from checkpoint!)

2. Configure settings:
   - Execution Mode: **Fork from Checkpoint**
   - Run ID to Resume: Enter the run ID from Step 1.4
   - New Run ID: Leave empty (auto-generated) or specify custom ID

3. Click "▶️ Start Execution"

4. The app will:
   - Load state from the first run
   - Apply the new repository's inferences
   - Start fresh execution history
   - Display success message with new run ID

### UI Flow

```
┌─────────────────────────────────────┐
│ Execution Mode                      │
├─────────────────────────────────────┤
│ ○ Fresh Run                         │
│ ○ Resume (PATCH)                    │
│ ○ Resume (OVERWRITE)                │
│ ○ Resume (FILL_GAPS)                │
│ ● Fork from Checkpoint              │ ← Select this
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Run ID to Resume                    │
│ [run-abc123...]                     │ ← Enter source run ID
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ New Run ID (optional)               │
│ [combination-run-001]               │ ← Optional: custom ID
└─────────────────────────────────────┘

         [▶️ Start Execution]
```

## What Happens During Forking

### State Transfer

✅ **Preserved:**
- Completed concept data (from Blackboard)
- Concept references (tensor data)
- Workspace state (loop counters, etc.)

🔄 **Reset:**
- Execution history
- Cycle count → 0
- Execution counters → 0
- Completion order

❌ **Not Preserved:**
- Inference item states (re-calculated for new repo)
- Waitlist (rebuilt from new repo)

### Reconciliation Mode

When forking, the app **defaults to OVERWRITE mode**, which:
- **Trusts checkpoint data completely**
- Keeps all values even if logic signatures differ
- Essential for repository chaining (e.g., `{new number pair}` from addition → combination)
- Prevents data loss when concepts have different signatures between repos

**You can change the reconciliation mode in Advanced Options:**

- **OVERWRITE** (default for Fork): Keeps all checkpoint data
  - ✅ Use for: Repository chaining, pipeline workflows
  - ⚠️ Caution: Ignores logic changes

- **PATCH** (default for Resume): Discards values with changed logic
  - ✅ Use for: Same repo with bug fixes
  - ⚠️ For forking: May discard needed data!

- **FILL_GAPS**: Only fills empty concepts
  - ✅ Use for: Importing partial results
  - ⚠️ For forking: May skip needed data!

## Example Workflows

### Example 1: Addition → Combination

**Goal**: Add two numbers, then combine the digits

**Files Needed:**
- Addition: `addition_concepts.json`, `addition_inferences.json`, `addition_inputs.json`
- Combination: `combination_concepts.json`, `combination_inferences.json`

**Steps:**

1. **Run Addition:**
   ```
   Upload: addition_concepts.json, addition_inferences.json, addition_inputs.json
   Mode: Fresh Run
   Execute → Note run ID: "addition-run-001"
   Result: {new number pair} = [['2', '2', '1'], ['1']]
   ```

2. **Fork to Combination:**
   ```
   Upload: combination_concepts.json, combination_inferences.json
   Mode: Fork from Checkpoint
   Run ID: "addition-run-001"
   New Run ID: (auto or "combine-001")
   Execute → Result: {sum} = "221"
   ```

### Example 2: Data Processing Pipeline

**Goal**: Load data → Process → Analyze → Visualize

**Files:**
- Stage 1: `load_concepts.json`, `load_inferences.json`, `data_inputs.json`
- Stage 2: `process_concepts.json`, `process_inferences.json`
- Stage 3: `analyze_concepts.json`, `analyze_inferences.json`
- Stage 4: `visualize_concepts.json`, `visualize_inferences.json`

**Steps:**

1. Run Stage 1 (Load) → `load-run-001`
2. Fork to Stage 2 (Process) from `load-run-001` → `process-run-001`
3. Fork to Stage 3 (Analyze) from `process-run-001` → `analyze-run-001`
4. Fork to Stage 4 (Visualize) from `analyze-run-001` → `visualize-run-001`

Each stage loads data from the previous stage automatically!

### Example 3: Testing Variations

**Goal**: Run same input through different processing strategies

**Files:**
- Base: `input_concepts.json`, `input_inferences.json`, `data.json`
- Variant A: `strategy_a_concepts.json`, `strategy_a_inferences.json`
- Variant B: `strategy_b_concepts.json`, `strategy_b_inferences.json`
- Variant C: `strategy_c_concepts.json`, `strategy_c_inferences.json`

**Steps:**

1. Run Base → `base-run-001`
2. Fork to Variant A from `base-run-001` → `variant-a-001`
3. Fork to Variant B from `base-run-001` → `variant-b-001`
4. Fork to Variant C from `base-run-001` → `variant-c-001`

Compare results from `variant-a-001`, `variant-b-001`, `variant-c-001`!

## Differences: Fork vs Resume

| Feature | Resume | Fork |
|---------|--------|------|
| **Run ID** | Same as source | New (different) |
| **Execution History** | Continues from checkpoint | Starts fresh |
| **Cycle Count** | Continues (e.g., 50→51) | Resets to 1 |
| **Repository** | Same or similar | Can be completely different |
| **Use Case** | Bug fixes, interrupted runs | Repository chaining |
| **Execution Counters** | Preserved | Reset to 0 |
| **Completion Order** | Preserved | Cleared |

## Advanced Options

### Custom New Run ID

By default, forking auto-generates a run ID like `fork-a1b2c3d4`. You can specify a custom ID:

```
New Run ID: my-combination-experiment-001
```

**Benefits:**
- Easier to identify in History tab
- Semantic naming (e.g., `addition-to-sum-v2`)
- Version tracking (e.g., `pipeline-run-001`, `pipeline-run-002`)

### Selecting Specific Checkpoint

By default, forking loads from the **latest** checkpoint of the source run. You can specify:

- **Specific run ID**: Enter exact run ID from History tab
- **Latest from any run**: Leave Run ID empty (uses latest overall)

## Troubleshooting

### "No checkpoint found"

**Issue**: App says checkpoint not found for specified run ID

**Solutions:**
1. Check the **History** tab for available run IDs
2. Verify database path matches (default: `orchestration.db`)
3. Ensure source run completed successfully
4. Try leaving Run ID empty to use latest

### "Concept not found in checkpoint"

**Issue**: New repository expects a concept that wasn't in the source checkpoint

**Solutions:**
1. Check that source run completed the required concepts
2. Review concept names (must match exactly)
3. Add missing concepts to inputs.json if needed
4. Check Results tab of source run to verify what concepts exist

### "Signature mismatch" warnings

**Issue**: App shows warnings about signature mismatches

**Explanation:** This is **normal and safe**! It means:
- The concept exists in both repos but with different logic
- PATCH mode will discard the old value and re-run
- This ensures the new repo's logic is used

**Action:** No action needed - this is expected when chaining different repositories

### "Data sufficiency" errors

**Issue**: Validation fails with missing ground concept data

**Solutions:**
1. Ensure source checkpoint has all required concepts
2. Check that concept names match between repos
3. Provide inputs.json for any missing ground concepts
4. Verify source run completed successfully

## Best Practices

### 1. Repository Design

✅ **Design for chaining**: Use clear, descriptive concept names  
✅ **Document dependencies**: Note which concepts are expected from previous stages  
✅ **Consistent naming**: Use same concept names across related repositories  

### 2. Run ID Management

✅ **Semantic naming**: Use descriptive new run IDs (`addition-v2`, not random)  
✅ **Version tracking**: Include version numbers (`pipeline-v1`, `pipeline-v2`)  
✅ **Date stamps**: Consider adding dates (`analysis-2025-11-30`)  

### 3. Checkpoint Hygiene

✅ **Verify completion**: Check Results tab before forking  
✅ **Export checkpoints**: Download important checkpoint states  
✅ **Clean old runs**: Remove obsolete runs from database periodically  

### 4. Error Handling

✅ **Test standalone**: Run each repository fresh first before chaining  
✅ **Check History**: Review source run in History tab before forking  
✅ **Export logs**: Download logs for debugging failed forks  

## Comparison with Python Script

The Streamlit app's forking feature matches the behavior of `ex_combine_standalone.py`:

| Feature | Script | App |
|---------|--------|-----|
| Load from checkpoint | `run_id="source"` | Run ID to Resume field |
| Create new run | `new_run_id="new"` | New Run ID field |
| Reconciliation mode | `mode="PATCH"` | Auto (PATCH) |
| Validation | `validate_compatibility=True` | Auto-enabled |
| Fresh history | Automatic | Automatic |

The app provides the same functionality with a visual interface!

## Summary

**Forking** enables powerful repository chaining workflows:
- ✅ Load completed concepts from one run
- ✅ Execute different repository on that data
- ✅ Start fresh execution history
- ✅ Build multi-stage pipelines
- ✅ Test variations without re-running expensive operations

Use the "Fork from Checkpoint" mode in the Streamlit app to connect your repositories together!

---

**Version**: 1.2  
**Date**: November 30, 2025  
**Related Docs**: 
- `REPOSITORY_COMPATIBILITY_IMPLEMENTATION.md` - Technical details
- `STREAMLIT_APP_GUIDE.md` - General app usage
- `ex_combine_standalone.py` - Python script example

