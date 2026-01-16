# Grouping Sequence

## Overview

The **Grouping Sequence** is a syntactic agent sequence that combines multiple references into a unified collection or relation. It is **deterministic, free (no LLM calls), and operates purely on data structure** without examining content semantics.

**Sequence Pattern**: `(IWI → IR → GR → OR → OWI)`

**Associated NormCode Operators**: 
- `&[{}]` (Group In / `&in`) - Creates labeled relations (dict-like)
- `&[#]` (Group Across / `&across`) - Creates flat collections (list-like)

---

## When to Use Grouping

Grouping is essential when you need to:

| Use Case | Operator | Example |
|----------|----------|---------|
| Collect named inputs for a function | `&[{}]` | Gather `{prompt}`, `{context}`, `{examples}` into one relation |
| Flatten a collection for iteration | `&[#]` | Combine digits from multiple numbers into a flat list |
| Build a dict-like structure | `&[{}]` | Package function parameters with their names |
| Concatenate multiple lists | `&[#]` | Merge results from parallel branches |
| Extract elements across an iteration | `&[#]` | Collect unit-place values from `{number pair}*1` |

---

## The Five-Step Pipeline

### Step 1: IWI (Input Working Interpretation)

**File**: `_iwi.py`

**Purpose**: Parse the syntax configuration from the working interpretation and initialize the states container.

**Key Operations**:
- Extract `marker` (`"in"` or `"across"`)
- Extract `by_axes` (per-reference axes to collapse, or legacy flat list)
- Extract `protect_axes` (axes to keep despite being in `by_axes`)
- Extract `create_axis` (name for the resulting axis dimension in `or_across`)
- Initialize placeholder records for downstream steps

**State Updates**:
```python
states.syntax.marker = "in" | "across"
states.syntax.by_axes = [["ax1"], ["ax2"]] | ["ax1", "ax2"]  # Per-ref or legacy
states.syntax.protect_axes = ["{axis_to_keep}", ...]
states.syntax.create_axis = "signal"  # For or_across mode
states.workspace = {...}  # From orchestrator
states.flow_index = "X.Y.Z"  # From orchestrator
```

---

### Step 2: IR (Input References)

**File**: `_ir.py`

**Purpose**: Load all concept references from the inference instance into the states container.

**Key Operations**:
- Retrieve **function concept** (the grouping operator itself)
- Retrieve **value concepts** (the items to be grouped)
- Retrieve **context concepts** (used to determine `by_axes`)
- Apply any injected filters
- Copy references (ensures independent storage [[memory:6376109]])

**State Updates**:
```python
states.function = [ReferenceRecordLite(...)]  # The grouping operator
states.values = [ReferenceRecordLite(...), ...]  # Items to group
states.context = [ReferenceRecordLite(...), ...]  # Axis information
```

**Note**: References are copied using `.copy()` to ensure storage independence [[memory:6376109]].

---

### Step 3: GR (Grouping References)

**File**: `_gr.py`

**Purpose**: Execute the core grouping logic by delegating to the `Grouper` class.

**Algorithm**:

1. **Determine `by_axes`** (backward compatible):
   - **New format**: If `states.syntax.by_axes` is provided (list of lists), use it directly
   - **Legacy format**: Derive from context concepts as before (flat list)
   - Remove any `protect_axes` from legacy `by_axes`

2. **Extract references**:
   - `value_refs`: References from all value concepts
   - `value_concept_names`: Names of value concepts (for annotation)
   - `create_axis`: Name for the output axis (for `or_across` mode)

3. **Invoke Grouper**:
   - If `marker == "in"`: Call `grouper.and_in()` → produces annotated dict-like structure
   - If `marker == "across"`: Call `grouper.or_across(by_axes, create_axis)` → produces flat list or new axis

4. **Store result**:
   - Save the grouped reference to `states.inference["GR"]`

**State Updates**:
```python
states.inference["GR"].reference = <grouped_reference>
```

---

### Step 4: OR (Output Reference)

**File**: `_or.py`

**Purpose**: Finalize the output by copying the GR result to the OR step.

**Key Operations**:
- Retrieve the reference from `states.inference["GR"]`
- Copy it to `states.inference["OR"]`

**State Updates**:
```python
states.inference["OR"].reference = states.inference["GR"].reference
```

---

### Step 5: OWI (Output Working Interpretation)

**File**: `_owi.py`

**Purpose**: Finalization step (currently a no-op for syntactic sequences).

**Key Operations**:
- Mark the step as complete
- Log completion

---

## The Two Grouping Modes

### Mode 1: `&[{}]` (Group In / `and_in`)

**Intuition**: Like putting items in a **labeled box**. Each item keeps its name/identity.

**Implementation**: `Grouper.and_in()`

**Process** (Per-Reference Mode with `create_axis`):
1. For each input reference, collapse the axes specified in `by_axes[i]`
2. Annotate each extracted element with its source concept name → `{concept_name: value}`
3. Concatenate all annotated elements
4. If `create_axis` is specified, wrap in that axis dimension

**Process** (Legacy Mode):
1. Find shared axes across all input references
2. Slice each reference to shared axes
3. Cross-product the sliced references
4. **Annotate** each element with its source concept name → creates `{name: value}` structure
5. Remove `by_axes` (collapse those dimensions)
6. Preserve `protect_axes` (keep those dimensions)

**Example (Legacy)**:

```ncd
{combined inputs}
    <= &[{}] %>[{prompt template}, {save path}] %:({input type}<$!{%(class)}>)
    <- {prompt template}
    <- {save path}
```

**Input**:
- `{prompt template}` = Reference with data `"Generate summary for {text}"`
- `{save path}` = Reference with data `"output/summary.txt"`

**Output** (dict-like):
```python
{
    "{prompt template}": "Generate summary for {text}",
    "{save path}": "output/summary.txt"
}
```

**Example (Per-Reference with create_axis)**:

```ncd
[all recommendations]
    <= &[{}] %>[{bullish recommendation}, {bearish recommendation}, {neutral recommendation}] %+(recommendation)
```

**Configuration**:
```python
{
    "by_axes": [["bullish_recommendation"], ["bearish_recommendation"], ["neutral_recommendation"]],
    "create_axis": "recommendation"
}
```

**Input**:
- `{bullish recommendation}` = Reference with data (axes: `[signal]`)
- `{bearish recommendation}` = Reference with data (axes: `[signal]`)
- `{neutral recommendation}` = Reference with data (axes: `[signal]`)

**Output**:
- Axes: `[recommendation]`, with annotated elements:
  ```python
  [
      {"{bullish recommendation}": value1},
      {"{bearish recommendation}": value2},
      {"{neutral recommendation}": value3}
  ]
  ```

**Use Cases**:
- Collecting function parameters with names (legacy)
- Building structured inputs for LLM calls (legacy)
- Creating configuration bundles (legacy)
- **Combining distinct recommendation branches into named collection** (new per-ref mode)

---

### Mode 2: `&[#]` (Group Across / `or_across`)

**Intuition**: Like pouring items from multiple containers into **one pile**. Items lose source identity but stay as a flat list.

**Implementation**: `Grouper.or_across()`

**Process** (New per-reference mode):
1. For each input reference, collapse the axes specified in `by_axes[i]`
2. Extract all resulting elements from each collapsed reference
3. Concatenate all elements into a single flat list
4. If `create_axis` is specified, wrap the list in a new axis dimension
5. Result size = sum of (product of collapsed axis sizes) for each input

**Process** (Legacy shared-axis mode):
1. Find shared axes across all input references
2. Slice each reference to shared axes
3. Cross-product the sliced references
4. Remove `by_axes` (collapse those dimensions)
5. **Flatten** all nested lists → single flat list

**Example (Legacy)**:

```ncd
{all unit place values}
    <= &[#] %>({number pair}*1) %:({number})
    <* {number pair}*1
```

**Input**:
- `{number pair}*1` = Reference with data `["123", "456"]` (axes: `[number]`)

**Output** (flat list):
```python
["3", "6"]  # Unit place digits flattened
```

**Example (Per-Reference with create_axis)**:

```ncd
{validated signal}
    <= &[#] %>[{quantitative signal}, {narrative signal}, {theoretical framework}] %+(signal)
```

Where `%+(signal)` explicitly names the new axis dimension.

**Configuration** (extracted from syntax):
```python
{
    "by_axes": [["quantitative_signal"], ["narrative_signal"], ["_none_axis"]],
    "create_axis": "signal"  # Extracted from %+(signal)
}
```

**Input**:
- `{quantitative signal}` = Reference with 2 items (axes: `[quantitative_signal]`)
- `{narrative signal}` = Reference with 1 item (axes: `[narrative_signal]`)
- `{theoretical framework}` = Reference with 1 item (axes: `[_none_axis]`)

**Output**:
- Axes: `[signal]`, Shape: `(4,)` with all 4 items concatenated

**Use Cases**:
- Flattening collections for iteration (legacy)
- Concatenating results from parallel operations (legacy)
- Extracting elements across a loop iteration (legacy)
- **Combining distinct concepts into a unified axis** (new per-ref mode)

---

## Axis Management: The Key to Understanding Grouping

### What are `by_axes`?

**`by_axes`** are axes that will be **removed** (collapsed) from the output reference.

Think of axes as dimensions in a tensor:
- A reference with axes `[student, class]` is a 2D structure
- Removing the `class` axis leaves only `[student]` - a 1D structure

### What are `protect_axes`?

**`protect_axes`** are axes that should be **kept** even if they appear in `by_axes`.

This is useful when:
- An axis is shared across inputs (would normally be collapsed)
- But you want to preserve that dimension in the output

### Example: Axis Collapse

```ncd
{grouped_results}
    <= &[#] %>({student_scores}) %:({class})
    <* {student_scores}  # Axes: [student, class, score]
```

**Before grouping**: 
- Axes: `[student, class, score]`

**After grouping** (remove `class` axis):
- Axes: `[student, score]`
- All values from different classes are now flattened together

### Example: Axis Protection

```ncd
{grouped_results}
    <= &[#] %>({student_scores}) %:({class}<$!{student}>)
    <* {student_scores}  # Axes: [student, class, score]
```

**Before grouping**: 
- Axes: `[student, class, score]`

**After grouping** (remove `class`, but protect `student`):
- Axes: `[student, score]`
- The `student` axis is preserved despite being in `by_axes`

---

## The Grouper Class (`infra/_syntax/_grouper.py`)

The actual grouping logic is implemented in the **`Grouper`** class, which provides tensor algebra operations:

### Core Methods

#### `and_in(references, annotation_list, by_axes, template, create_axis)`

**Purpose**: Create a labeled relation (dict-like structure)

**Parameters**:
- `references`: List of Reference objects to combine
- `annotation_list`: List of concept names (for labeling)
- `by_axes`: Either:
  - `List[List[str]]`: Per-reference axes to collapse (e.g., `[["ax1"], ["ax2"]]`)
  - `List[str]`: Shared axes to collapse (legacy, e.g., `["ax1", "ax2"]`)
- `template`: Optional string template for formatting
- `create_axis`: Optional name for the resulting axis dimension

**Returns**: Reference with dict-like annotated elements

**Backward Compatibility**:
- If `by_axes` is a flat list and `create_axis` is specified, the flat list is broadcast to all references
- If `by_axes` is a flat list and `create_axis` is NOT specified, uses legacy cross-product + annotate
- If `by_axes` is a list of lists, uses per-reference collapse mode

**Algorithm** (Per-Reference Mode):
```python
1. For each reference, collapse the specified axes in by_axes[i]
2. Annotate each element with {concept_name: value}
3. Concatenate all annotated elements
4. Create new Reference with create_axis as dimension
5. Apply template if provided
```

**Algorithm** (Legacy Mode):
```python
1. Find shared axes across all references
2. Slice each reference to shared axes (alignment)
3. Cross-product to combine aligned elements
4. Annotate each element with {name: value} structure
5. Remove by_axes (collapse dimensions)
6. Apply template if provided
```

---

#### `or_across(references, by_axes, template, create_axis)`

**Purpose**: Create a flat collection or a new axis dimension

**Parameters**:
- `references`: List of Reference objects to combine
- `by_axes`: Either:
  - `List[List[str]]`: Per-reference axes to collapse (e.g., `[["ax1"], ["ax2"]]`)
  - `List[str]`: Shared axes to collapse (legacy, e.g., `["ax1", "ax2"]`)
- `template`: Optional string template for formatting
- `create_axis`: Optional name for the resulting axis dimension

**Returns**: Reference with flat list elements or new axis

**Backward Compatibility**:
- If `by_axes` is a flat list and `create_axis` is specified, the flat list is broadcast to all references
- If `by_axes` is a flat list and `create_axis` is NOT specified, uses legacy cross-product + flatten
- If `by_axes` is a list of lists, uses per-reference collapse mode

**Algorithm** (Per-Reference Mode):
```python
1. For each reference, collapse the specified axes in by_axes[i]
2. Extract all elements using slice + _get_leaves
3. Concatenate all extracted elements
4. Create new Reference with create_axis as dimension
5. Apply template if provided
```

**Algorithm** (Legacy Mode):
```python
1. Find shared axes across all references
2. Slice each reference to shared axes (alignment)
3. Cross-product to combine aligned elements
4. Remove by_axes (collapse dimensions)
5. Flatten all nested lists into a single flat list
6. Apply template if provided
```

---

### Helper Methods

#### `find_share_axes(references)`

Finds axes that are common across all input references.

**Example**:
- Ref A: `[student, class]`
- Ref B: `[student, score]`
- Shared: `[student]`

---

#### `flatten_element(reference)`

Recursively flattens nested lists within each element of a reference.

**Example**:
- Input: `[[1, 2], [3, 4]]`
- Output: `[1, 2, 3, 4]`

---

#### `annotate_element(reference, annotation_list)`

Transforms list elements into dict elements with concept names as keys.

**Example**:
- Input: `[val1, val2]` with annotations `["{A}", "{B}"]`
- Output: `{"{A}": val1, "{B}": val2}`

---

## Real-World Example: Base-X Addition

From the NormCode base-X addition algorithm, here's how grouping is used to extract digit values:

```ncd
[all {unit place value} of numbers] | 1.1.2.4
    <= &across({unit place value}:{number pair}*1)
    <- {unit place value} | 1.1.2.4.2
        <= *every({number pair}*1)%:[{number}]@(2)
            <= $.({single unit place value})
            <- {single unit place value} | 1.1.2.4.2.1.2
                <= ::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)
                <- {unit place digit}?<:{2}>
                <- {number pair}*1*2
        <- {number pair}*1
```

**What happens**:

1. **Inner loop** (`*every`) extracts the unit place value from each number in `{number pair}*1`
2. **Grouping** (`&across`) collects those values into a flat list
3. **Result**: A list of digits ready to be summed

**Concretely**:
- Input: `{number pair}*1` = `["123", "456"]`
- After extraction: `[{unit place value}, {unit place value}]` = `["3", "6"]`
- After grouping: `[all {unit place value} of numbers]` = `["3", "6"]` (flat list)

---

## Syntax Extraction

The grouping sequence expects the following structure in `working_interpretation`:

```python
{
    "syntax": {
        "marker": "in" | "across",
        # Legacy format (for and_in or old or_across)
        "by_axis_concepts": ["{concept1}", "{concept2}", ...],  # Optional
        # New format (for or_across with per-ref collapse)
        "by_axes": [["ax1"], ["ax2"], ["ax3"]],  # Per-reference axes
        "create_axis": "signal",  # Extracted from %+(signal) modifier
        "protect_axes": ["{axis1}", "{axis2}", ...]  # Optional
    },
    "workspace": {...},  # From orchestrator
    "flow_info": {
        "flow_index": "X.Y.Z"
    }
}
```

### Modifier Extraction

The `create_axis` field is extracted from the `%+` modifier in the function concept:

| Syntax Pattern | Extracted Field | Example Value |
|----------------|-----------------|---------------|
| `%+(signal)` | `create_axis` | `"signal"` |
| `%+({validated signal})` | `create_axis` | `"validated signal"` |

### NormCode Syntax Mapping

| Old Syntax | New Syntax | Marker | Description |
|------------|------------|--------|-------------|
| `&in` | `&[{}] %>[...]` | `"in"` | Group into labeled relation (legacy) |
| N/A | `&[{}] %>[...] %+({axis})` | `"in"` | Collapse per-ref + annotate + create axis |
| `&across({item}:{src})` | `&[#] %>({src}) %:({item})` | `"across"` | Flatten across axis (legacy) |
| N/A | `&[#] %>[...] %+({axis})` | `"across"` | Collapse per-ref + create axis |

---

## Configuration in AgentFrame

The grouping sequence is registered and configured in the AgentFrame:

**Setup** (`set_up_grouping_demo`):
- Registers the `grouping` sequence decorator
- Defines the 5-step pipeline: `(IWI-IR-GR-OR-OWI)`

**Configuration** (`configure_grouping_demo`):
- Maps each step name to its implementation method
- Methods come from the `grouping_methods` dict in `__init__.py`

**Invocation**:
```python
from infra._agent._steps.grouping import grouping_methods

agent_frame.configure_inference(
    inference_instance,
    sequence="grouping",
    methods=grouping_methods
)
```

---

## Key Design Principles

### 1. Context-Agnostic

Grouping doesn't care about the **meaning** of the data. It only cares about:
- Reference shapes (axes)
- Which axes to collapse
- Whether to annotate or flatten

This makes it:
- **Free**: No LLM calls
- **Deterministic**: Same input → same output, always
- **Auditable**: Trace exactly what structure changed

---

### 2. Reference Independence

The IR step copies all references using `.copy()` [[memory:6376109]]. This ensures:
- Grouping operations don't mutate original references
- Parallel inferences can safely share concepts
- Rollback and checkpointing work correctly

---

### 3. Axis-Centric Logic

Grouping is fundamentally about **axis manipulation**:
- **Cross-product**: Align references on shared axes
- **Slice**: Project onto specific axes
- **Collapse**: Remove axes from the output

This tensor-algebra approach makes grouping composable and predictable.

---

### 4. Subject-Agnostic

Unlike semantic sequences (imperative, judgement), grouping doesn't require a specific "Body" or Subject (`:S:`). It operates on the **structure** of references, not their **content**.

This universality means:
- Grouping works identically across all AgentFrames
- No tool invocation required
- No paradigm configuration needed

---

## Troubleshooting

### Problem: Empty output reference

**Cause**: All `by_axes` removed all dimensions

**Solution**: 
- Check that you're not collapsing all axes
- Use `protect_axes` to keep essential dimensions

---

### Problem: Nested lists not flattening in `&[#]`

**Cause**: The `flatten_element` method is recursive

**Solution**:
- Verify input references have the expected shape
- Check that cross-product is creating the structure you expect

---

### Problem: Missing annotations in `&[{}]`

**Cause**: `annotation_list` length doesn't match number of references

**Solution**:
- Ensure every value concept has a unique name
- Check that IR step loaded all value concepts correctly

---

## Testing Checklist

When implementing or modifying grouping, verify:

- [ ] IWI extracts `marker`, `by_axis_concepts`, `protect_axes` correctly
- [ ] IR loads all value and context concepts with references
- [ ] GR computes `by_axes` correctly (flatten, deduplicate, protect)
- [ ] `&[{}]` produces dict-like structure with concept names as keys
- [ ] `&[#]` produces flat list with no nesting
- [ ] Axes are removed/preserved as specified
- [ ] References are copied (not mutated)
- [ ] Logging provides clear debugging info at each step

---

## Related Documentation

- **NormCode Formalism**: See `context_store/shared---normcode_formalism_basic.md`
- **Agent Sequences Guide**: See `context_store/shared---normcode_agent_sequence_guide.md`
- **Syntactic Operators**: See `context_store/shared---normcode_syntatical_concepts_reconstruction.md`
- **Reference System**: See paper draft Section 4.1-4.3

---

## Summary

The Grouping Sequence is a **syntactic tensor algebra operator** that:

✅ Combines multiple references into unified collections  
✅ Operates deterministically without LLM calls (free, fast)  
✅ Supports two modes: labeled relations (`&[{}]`) and flat lists (`&[#]`)  
✅ Manages axes explicitly (collapse, preserve, protect)  
✅ Integrates seamlessly with loops, assignments, and semantic sequences  

**When in doubt**: 
- Use `&[{}]` when you need to **access items by name later**
- Use `&[#]` when you just need **all items together**

