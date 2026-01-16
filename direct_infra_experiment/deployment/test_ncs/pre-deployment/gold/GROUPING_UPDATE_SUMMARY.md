# NormCode Grouping System Update - Session Summary
**Date**: December 14, 2025  
**System**: Gold Investment Decision System (NormCode Framework)  
**Focus**: Grouping Sequence Per-Reference Collapse Mode Implementation

---

## Executive Summary

We implemented a **new per-reference collapse mode** for the grouping sequence to handle the axis shape mismatch problem in the Gold Investment System. The key innovation is the `%+({axis_name})` modifier syntax and `by_axes` as a list of per-reference axes to collapse.

**Implementation Status**: ✅ Code Complete, ⏳ Testing Pending  
**Files Modified**: 8 implementation files + 3 documentation files  
**Backward Compatibility**: ✅ Maintained (legacy mode still works)

---

## The Original Problem

### Symptom
All three recommendation inferences (1.9.1.1, 1.9.1.2, 1.9.1.3) were failing with JSON parsing errors during `cross_action`:

```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

### Root Cause
The grouping step (inference 1.5) was creating `{validated signal}` with the wrong shape:

**Expected**:
```python
axes: ['signal']
shape: (3,)  # 3 separate elements: quantitative, narrative, framework
```

**Actual** (before fix):
```python
axes: ['_none_axis']
shape: (1,)
tensor: [[item1, item2, item3]]  # All items nested in single cell
```

### Why This Failed
When bullish/bearish recommendations tried to combine:
- `{validated signal}` (wrongly structured)
- `{investor risk profile}` (axes: `['_none_axis']`)

The `cross_action` couldn't align axes properly, causing the MVPstep to receive malformed data, which then produced invalid JSON responses from the LLM.

---

## The Solution: Per-Reference Collapse Mode

### Conceptual Model

**Problem**: How do you combine **distinct concepts** with **different axis structures** into a **unified axis**?

**Example**: 
- `{quantitative signal}` has `axes: ['quantitative_signal']`
- `{narrative signal}` has `axes: ['narrative_signal']`
- Want result: `{validated signal}` with `axes: ['signal']` containing both

**Legacy grouping** (`&[#]` or `&[{}]`) used cross-product + flatten, which works for:
- Concepts with **shared axes** (align and combine)
- Creating nested structures

But **doesn't work** for:
- Distinct concepts with different axes
- Creating a new unified axis dimension

### New Approach: Per-Reference Collapse + Concatenate

**Algorithm**:
1. For each input reference, collapse its specified axes independently
2. Extract all resulting elements
3. Concatenate all elements into a flat list
4. Wrap in a new axis with the specified name

**Syntax**: `%+({axis_name})` explicitly names the new axis

---

## Implementation Details

### 1. **New Syntax: `%+` Modifier**

Added to the unified modifier system:

| Modifier | Name | Meaning |
|----------|------|---------|
| `%+` | Create | New axis to create |

**Usage**:
```ncd
{validated signal}
    <= &[#] %>[{quantitative signal}, {narrative signal}] %+(signal)
```

The `%+(signal)` explicitly indicates "create a new 'signal' axis".

---

### 2. **Configuration Format**

**New `working_interpretation` structure**:

```python
{
    "syntax": {
        "marker": "across",  # or "in"
        "by_axes": [
            ["quantitative_signal"],  # Collapse this from input 0
            ["narrative_signal"]      # Collapse this from input 1
        ],
        "create_axis": "signal"       # Name for the new axis
    }
}
```

**Key Changes**:
- `by_axes`: Changed from `List[str]` to `List[List[str]]` (per-reference)
- `create_axis`: New parameter for explicit axis naming

---

### 3. **Implementation Changes**

#### A. `infra/_syntax/_grouper.py`

**Updated both `or_across()` and `and_in()` methods**:

```python
def or_across(
    self, 
    references: List[Reference], 
    by_axes: Optional[List] = None,  # List[str] OR List[List[str]]
    template: Optional[Template] = None,
    create_axis: Optional[str] = None
) -> Reference:
```

**Key Logic**:
1. **Detect mode**: Check if `by_axes[0]` is a list → per-ref mode
2. **Normalize**: Flat list + `create_axis` → broadcast to all refs
3. **Execute**:
   - Per-ref mode: collapse each input → concatenate → wrap in `create_axis`
   - Legacy mode: cross-product → flatten (unchanged)

**Per-Reference Implementation**:
```python
for i, ref in enumerate(references):
    axes_to_collapse = by_axes[i] if i < len(by_axes) else list(ref.axes)
    preserve_axes = [ax for ax in ref.axes if ax not in axes_to_collapse]
    
    if preserve_axes:
        sliced = ref.slice(*preserve_axes)
        elements = list(sliced._get_leaves())
    else:
        elements = list(ref._get_leaves())
    
    all_elements.extend(elements)

result = Reference(axes=[create_axis], shape=(len(all_elements),))._replace_data(all_elements)
```

---

#### B. `infra/_agent/_steps/grouping/_iwi.py`

**Reads new parameters from `working_interpretation`**:

```python
states.syntax.by_axes = working_interpretation.get("syntax", {}).get("by_axes")
states.syntax.create_axis = working_interpretation.get("syntax", {}).get("create_axis")
```

---

#### C. `infra/_agent/_steps/grouping/_gr.py`

**Passes new parameters to grouper**:

```python
if per_ref_by_axes is not None:
    by_axes_for_grouper = per_ref_by_axes  # List[List[str]]
else:
    by_axes_for_grouper = legacy_by_axes    # List[str]

# For or_across
result_ref = grouper.or_across(
    value_refs,
    by_axes=by_axes_for_grouper,
    create_axis=create_axis,
)

# For and_in
result_ref = grouper.and_in(
    value_refs,
    value_concept_names,
    by_axes=by_axes_for_grouper,
    create_axis=create_axis,
)
```

---

### 4. **Backward Compatibility**

**Three configuration formats are supported**:

| Format | `by_axes` | `create_axis` | Mode Triggered |
|--------|-----------|---------------|----------------|
| Legacy | `None` or flat list | `None` | Legacy cross-product + flatten |
| Broadcast | Flat list | Specified | Per-ref (same axes for all) |
| Per-ref | List of lists | Specified | Per-ref (different axes per input) |

**Examples**:

```python
# Legacy: cross-product + flatten
{"marker": "across", "by_axis_concepts": [...]}

# Broadcast: same axes for all inputs
{"marker": "across", "by_axes": ["axis1"], "create_axis": "result"}

# Per-ref: different axes per input
{"marker": "across", "by_axes": [["ax1"], ["ax2"], ["ax3"]], "create_axis": "result"}
```

---

## Repository Updates

### Updated Inferences

**1. Inference 1.5 - `{validated signal}`** (`&[#]` per-ref mode):

```json
{
    "function_concept": "&[#] %>[{quantitative signal}, {narrative signal}] %+(signal)",
    "working_interpretation": {
        "syntax": {
            "marker": "across",
            "by_axes": [
                ["quantitative_signal"],
                ["narrative_signal"]
            ],
            "create_axis": "signal"
        }
    }
}
```

**2. Inference 1.8.1 - `<signal status>`** (legacy mode with protect_axes):

```json
{
    "function_concept": "&[#] %>[<signals surpass...>, <signals deviate...>] %^<$!={signal}>",
    "working_interpretation": {
        "syntax": {
            "marker": "across",
            "protect_axes": ["signal"]
        }
    }
}
```

**Note**: Removed incorrect `by_axes: [["_none_axis"], ["_none_axis"]]` because both inputs actually have `axes: ["signal"]`, not `["_none_axis"]`.

**3. Inference 1.9.1 - `[all recommendations]`** (`&[{}]` per-ref mode):

```json
{
    "function_concept": "&[{}] %>[{bullish...}, {bearish...}, {neutral...}] %+(recommendation)",
    "working_interpretation": {
        "syntax": {
            "marker": "in",
            "by_axes": [
                ["bullish_recommendation"],
                ["bearish_recommendation"],
                ["neutral_recommendation"]
            ],
            "create_axis": "recommendation"
        }
    }
}
```

---

## Documentation Updates

### 1. `infra/_agent/_steps/grouping/README.md`
- Added per-reference mode documentation for both `&[#]` and `&[{}]`
- Updated `or_across()` and `and_in()` method signatures
- Added examples showing both modes
- Updated syntax mapping table

### 2. `shared---normcode_activation.md`
- Updated grouping modes table
- Added Example 2b (Group In with per-ref collapse)
- Added Example 4 (Group Across with per-ref collapse)
- Documented extraction patterns for `%+` modifier

### 3. `shared---normcode_syntatical_concepts_reconstruction.md`
- Updated modifier reference table to include `%+`
- Enhanced Group In and Group Across sections
- Added per-reference examples
- Updated extraction format documentation

---

## Files Modified

### Implementation (8 files)
1. `infra/_syntax/_grouper.py` - Core grouping logic
2. `infra/_agent/_steps/grouping/_iwi.py` - Parameter extraction
3. `infra/_agent/_steps/grouping/_gr.py` - Parameter passing
4. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/repos/inference_repo.json` - Updated 3 inferences
5. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/repos/concept_repo.json` - Updated 3 functional concepts

### Documentation (3 files)
6. `infra/_agent/_steps/grouping/README.md`
7. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared---normcode_activation.md`
8. `direct_infra_experiment/nc_ai_planning_ex/iteration_6/context_store/shared---normcode_syntatical_concepts_reconstruction.md`

---

## Testing Status

### ⏳ Pending: Execution Test

**Command**:
```powershell
python direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/_executor.py
```

**Expected Results**:
1. ✅ Inference 1.5 creates `{validated signal}` with `axes: ['signal'], shape: (2,)`
2. ✅ Inferences 1.9.1.1 and 1.9.1.2 successfully combine `{validated signal}` + `{investor risk profile}`
3. ✅ All 20 inferences complete successfully
4. ✅ Final `{investment decision}` is produced

**Key Validation Points**:
- [ ] `{validated signal}` has correct axes and shape
- [ ] Cross-action succeeds for recommendation inferences
- [ ] LLM receives properly formatted data
- [ ] JSON parsing succeeds (no more "Expecting value" errors)
- [ ] Final decision is synthesized

---

## Comparison: Before vs After

### Inference 1.5 Configuration

**Before** (incorrect):
```python
{
    "by_axis_concepts": ["{quantitative signal}", "{narrative signal}", "{theoretical framework}"],
    "protect_axes": []
}
```
- Used concept names instead of axis names
- All 3 inputs grouped together
- Created nested list in single cell

**After** (correct):
```python
{
    "by_axes": [["quantitative_signal"], ["narrative_signal"]],
    "create_axis": "signal"
}
```
- Uses actual axis names from references
- Only 2 inputs (removed `{theoretical framework}` based on user's repo changes)
- Creates proper `signal` axis with 2 elements

### Inference 1.9.1 Configuration

**Before**:
```python
{
    "marker": "in",
    "by_axis_concepts": ["{bullish...}", "{bearish...}", "{neutral...}"]
}
```

**After**:
```python
{
    "marker": "in",
    "by_axes": [["bullish_recommendation"], ["bearish_recommendation"], ["neutral_recommendation"]],
    "create_axis": "recommendation"
}
```

---

## Design Decisions

### 1. Why `%+` for axis creation?

**Rationale**: 
- Consistent with unified modifier system (`%>`, `%<`, `%:`, `%^`, `%@`)
- Mnemonic: `+` = "add a new dimension"
- Explicit: Makes axis creation visible in NormCode syntax
- Distinguishable from `protect_axes` (preserve existing) vs `create_axis` (create new)

### 2. Why `by_axes` as List[List[str]]?

**Rationale**:
- Each input reference may have different axes
- Per-reference specification allows fine-grained control
- Aligns with the "collapse independently then concatenate" algorithm
- Natural extension of existing `by_axes` concept

### 3. Why keep legacy mode?

**Rationale**:
- Existing code relies on cross-product + flatten behavior
- Inference 1.8.1 (`<signal status>`) uses `protect_axes` legitimately
- Backward compatibility prevents breaking existing systems
- Clear separation: per-ref mode for **distinct concepts**, legacy for **shared axes**

---

## Key Insights

### Semantic Difference: Unify vs Preserve

**Per-Reference Mode** (`%+`):
- **Purpose**: Unify distinct concepts with different structures
- **Example**: Combine quantitative_signal + narrative_signal → signal axis
- **Axes**: Different axes from each input, create new unified axis
- **Use case**: Merging heterogeneous data sources

**Legacy Mode** (`%^<$!>`):
- **Purpose**: Preserve shared axes while grouping
- **Example**: Stack truth masks while keeping signal axis
- **Axes**: Same shared axes across inputs, protect from collapse
- **Use case**: Grouping homogeneous data with common dimensions

### The "Collapse-Concat-Promote" Pattern

This pattern emerged as the natural solution for combining distinct concepts:

1. **Collapse**: Remove each input's specific axes (e.g., `quantitative_signal`, `narrative_signal`)
2. **Concat**: Merge all resulting elements into a flat list
3. **Promote**: Wrap the list in a new named axis (e.g., `signal`)

This is **tensor algebra for AI planning** - reshaping data structures to enable downstream operations.

---

## Remaining Questions

### 1. Should we add logging for debugging?

**Options**:
- Add `logging.debug()` calls in `_grouper.py` to show mode selection and axes
- Keep code clean and rely on external debugging
- Add only when `dev_mode=True`

### 2. Should `protect_axes` work with per-ref mode?

**Current**: `protect_axes` only works in legacy mode  
**Question**: Does it make sense to protect axes in per-ref mode?  
**Decision**: No - per-ref mode explicitly specifies which axes to collapse, making protection redundant

### 3. Should we validate `by_axes` length matches references?

**Current**: Code handles mismatch gracefully (uses default if `i >= len(by_axes)`)  
**Question**: Should we raise an error if lengths don't match?  
**Decision**: Current behavior is flexible, but could add warning log

---

## Success Metrics

**Implementation**: ✅ Complete  
**Documentation**: ✅ Complete  
**Testing**: ⏳ Pending  

**Target Outcomes**:
- [ ] All 20 inferences complete
- [ ] No axis shape mismatches
- [ ] No JSON parsing errors
- [ ] `{investment decision}` successfully synthesized
- [ ] 100% success rate

---

## Next Steps

1. **Run executor** and collect new logs
2. **Verify** `{validated signal}` has correct structure
3. **Confirm** recommendation inferences succeed
4. **Review** final output quality
5. **Document** any additional issues discovered

---

**End of Summary**

