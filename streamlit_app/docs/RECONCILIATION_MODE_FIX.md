# Reconciliation Mode Fix - Fork vs Resume

## Problem Identified

When testing the forking feature (Addition → Combination), the execution failed with:

```
[ERROR] Ground concept '&across({new number pair}:{new number pair}<--<!_>>)' is missing data
```

### Root Cause

The app was using **PATCH mode** for forking, which:
1. Compared logic signatures between repos
2. Found that `{new number pair}` had different signatures (addition vs combination)
3. **Discarded** `{new number pair}` from checkpoint due to signature mismatch
4. Combination repo tried to run but had no input data → ERROR

## Solution

### Separation of Concerns

**Before (v1.2.0 initial):**
```
Execution Mode:
  ○ Fresh Run
  ○ Resume (PATCH)      ← Mode baked into choice
  ○ Resume (OVERWRITE)  ← Mode baked into choice
  ○ Resume (FILL_GAPS)  ← Mode baked into choice
  ● Fork from Checkpoint ← Hardcoded to PATCH
```

**After (v1.2.0 fixed):**
```
Execution Mode:
  ○ Fresh Run
  ○ Resume from Checkpoint
  ● Fork from Checkpoint

Advanced Options > Reconciliation Mode:
  ○ PATCH (default for Resume)
  ● OVERWRITE (default for Fork)
  ○ FILL_GAPS
```

### Benefits

✅ **Simpler UI**: 3 execution modes instead of 5  
✅ **Smart Defaults**: PATCH for Resume, OVERWRITE for Fork  
✅ **User Control**: Can override defaults in Advanced Options  
✅ **Clear Semantics**: Execution type vs State reconciliation  

## Why OVERWRITE for Forking?

### The Issue

When chaining repositories (A → B), concepts often have **different signatures**:
- Addition repo defines `{new number pair}` as output (result of addition)
- Combination repo defines `{new number pair}` as input (to be combined)
- **Same name, different role** → Different signatures

### PATCH Mode Behavior

```
PATCH mode logic:
  if checkpoint_signature != repo_signature:
      discard checkpoint value  # ❌ Loses required data!
      mark concept as pending
```

**Result**: Combination repo has no input data → Execution fails

### OVERWRITE Mode Behavior

```
OVERWRITE mode logic:
  Keep all checkpoint values
  Ignore signature differences  # ✅ Preserves data!
```

**Result**: Combination repo gets `{new number pair}` → Execution succeeds

## When to Use Each Mode

| Mode | Best For | Fork? | Resume? |
|------|----------|-------|---------|
| **OVERWRITE** | Repository chaining | ✅ Default | ⚠️ Use with caution |
| **PATCH** | Bug fixes in same repo | ⚠️ May lose data | ✅ Default |
| **FILL_GAPS** | Partial data import | ⚠️ May skip data | ✅ Safe |

### Use Cases

#### OVERWRITE (Default for Fork)

✅ **Repository Chaining**: Addition → Combination → Analysis  
✅ **Pipeline Workflows**: Load → Process → Analyze → Visualize  
✅ **Testing Variations**: Same input, different processing repos  

❌ **Avoid for**: Same repo with logic changes (may use stale results)

#### PATCH (Default for Resume)

✅ **Bug Fixes**: Fixed one prompt, want to re-run that step  
✅ **Logic Changes**: Updated algorithm, keep valid data  
✅ **Development**: Iterating on same repository  

❌ **Avoid for**: Different repositories (may discard needed data)

#### FILL_GAPS

✅ **Partial Import**: Want some checkpoint data, prefer new defaults  
✅ **Conservative Merge**: Only fill truly empty concepts  

❌ **Avoid for**: Complete data transfer

## Technical Implementation

### UI Flow

```python
# Step 1: User selects execution mode
resume_option = st.radio(
    "Execution Mode",
    ["Fresh Run", "Resume from Checkpoint", "Fork from Checkpoint"]
)

# Step 2: If Resume/Fork, Advanced Options shows reconciliation mode
if resume_option != "Fresh Run":
    # Smart default based on execution mode
    if resume_option == "Fork from Checkpoint":
        default = "OVERWRITE"  # ← Key fix!
    else:
        default = "PATCH"
    
    reconciliation_mode = st.radio(
        "How to apply checkpoint state:",
        ["PATCH", "OVERWRITE", "FILL_GAPS"],
        index=mode_options.index(default)
    )

# Step 3: Use selected mode
orchestrator = Orchestrator.load_checkpoint(
    ...,
    mode=reconciliation_mode  # User's choice
)
```

### State Transfer Comparison

#### With OVERWRITE (Fixed)

```
Addition Checkpoint:
  {new number pair} = [['2','2','1'], ['1']]  (signature: abc123)

Combination Repo:
  {new number pair} expected as input  (signature: def456)

OVERWRITE mode:
  ✅ Keep [['2','2','1'], ['1']] despite signature mismatch
  ✅ Combination repo has input data
  ✅ Execution succeeds → {sum} = "221"
```

#### With PATCH (Broken)

```
Addition Checkpoint:
  {new number pair} = [['2','2','1'], ['1']]  (signature: abc123)

Combination Repo:
  {new number pair} expected as input  (signature: def456)

PATCH mode:
  ❌ Signature mismatch detected
  ❌ Discard checkpoint value
  ❌ Mark as pending
  ❌ No input data for combination repo
  ❌ ERROR: Missing ground concept data
```

## Files Modified

1. **`streamlit_app/app.py`**
   - Simplified execution mode options (5 → 3)
   - Moved reconciliation mode to Advanced Options
   - Added smart defaults (OVERWRITE for Fork, PATCH for Resume)
   - Updated help text

2. **`streamlit_app/FORKING_GUIDE.md`**
   - Explained OVERWRITE as default for forking
   - Documented when to use each mode
   - Added warnings about mode selection

3. **`streamlit_app/CHANGELOG.md`**
   - Documented reconciliation mode separation
   - Listed smart defaults

4. **`streamlit_app/RECONCILIATION_MODE_FIX.md`**
   - This document

## Testing

### Test Case: Addition → Combination

**Before Fix (PATCH mode):**
```
❌ ERROR: Ground concept '&across({new number pair}...' missing data
❌ Execution failed at Cycle 1
```

**After Fix (OVERWRITE mode):**
```
✅ State loaded from addition checkpoint
✅ {new number pair} preserved
✅ Combination inferences executed
✅ {sum} = "221"
```

### Verification

Run the following to test:

1. **Run Addition:**
   - Upload: `addition_concepts.json`, `addition_inferences.json`, `addition_inputs.json`
   - Mode: Fresh Run
   - Note Run ID

2. **Fork to Combination:**
   - Upload: `combination_concepts.json`, `combination_inferences.json`
   - Mode: Fork from Checkpoint
   - Run ID: Enter addition run ID
   - Advanced Options: Verify OVERWRITE is selected (default)
   - Execute → Should succeed!

3. **Test PATCH Override:**
   - Same as step 2, but change reconciliation mode to PATCH
   - Execute → Should fail (expected behavior)

## Conclusion

The fix separates **execution semantics** (Fresh/Resume/Fork) from **reconciliation strategy** (PATCH/OVERWRITE/FILL_GAPS), providing:

✅ **Cleaner UI** - 3 main modes instead of 5  
✅ **Smart Defaults** - OVERWRITE for Fork (preserves data)  
✅ **User Control** - Can override in Advanced Options  
✅ **Working Pipelines** - Addition → Combination now succeeds  

---

**Version**: 1.2.0 (fixed)  
**Date**: November 30, 2025  
**Status**: ✅ Tested and working  
**Credit**: User feedback from terminal logs

