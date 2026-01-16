# Judgement in Composition Sequence

## Purpose

The `judgement_in_composition` sequence provides a flexible method for executing complex evaluation and assertion logic using declaratively defined **paradigms**, with an additional **TIA (Tool Inference Assertion)** step that transforms results into truth masks based on quantified conditions.

This sequence is ideal for scenarios where you need to:
1. Evaluate conditions across multi-dimensional data (e.g., "for each document where SOME paragraph mentions X")
2. Apply complex judgement logic defined in paradigms
3. Produce truth masks that preserve data structure for downstream filtering

## Sequence Flow

```
IWI → IR → MFP → MVP → TVA → TIA → OR → OWI
```

### Key Difference from Imperative Sequence

Unlike `imperative_in_composition`, this sequence includes the **TIA (Tool Inference Assertion)** step, which:
- Takes the output from TVA
- Applies quantified assertions (all, some, none, exists, for-each)
- Produces a **truth mask** with `%{truth value}(true/false)` markers
- Enables hierarchical collapsing for complex multi-axis filtering

## Workflow

### 1. **IWI (The Planner - `_iwi.py`)**
   - Reads the `working_interpretation` to get:
     - `paradigm`: The judgement paradigm to load (e.g., `"document_relevance_check"`)
     - `assertion_condition`: The quantifiers and conditions for TIA
   - Loads the paradigm's `env_spec` and `sequence_spec`
   - Stores `assertion_condition` for the TIA step

### 2. **IR (Input References - `_ir.py`)**
   - Gathers initial data references from input concepts

### 3. **MFP (The Composer - `_mfp.py`)**
   - Executes the paradigm's `sequence_spec`
   - Resolves tool affordances (e.g., `"llm.generate"`) into a composed function
   - The function encapsulates the judgement logic

### 4. **MVP (The Data Pre-processor - `_mvp.py`)**
   - Gathers and transforms input data
   - Uses `value_order` to structure inputs correctly
   - Processes wrappers (e.g., `%{file_location}(path)`)

### 5. **TVA (The Executor - `_tva.py`)**
   - Executes the composed function with prepared data
   - Produces initial evaluation results (typically boolean values)

### 6. **TIA (The Assertor - `_tia.py`)** ← NEW STEP
   - **Primary Innovation**: Applies quantified assertions to TVA output
   - Transforms results into truth masks
   - Supports hierarchical collapsing (e.g., "for each document where SOME paragraph")
   - Produces structured truth value markers: `%{truth value}(true)` / `%{truth value}(false)`

### 7. **OR & OWI (Output Steps)**
   - OR retrieves the truth mask from TIA (not TVA!)
   - Returns the structured truth mask for downstream use

## Configuration (`working_interpretation`)

### Basic Structure

```json
{
  "paradigm": "judgement_paradigm_name",
  "value_order": {
    "concept_name": 0,
    "another_concept": 1
  },
  "assertion_condition": {
    "quantifiers": {
      "axis_name": "quantifier_type"
    },
    "condition": true
  }
}
```

### Key Parameters

- **`paradigm`** (required): The judgement paradigm to execute
- **`value_order`**: Maps input concepts to paradigm inputs
- **`assertion_condition`** (optional but recommended): Defines how to assert truth conditions

## The TIA Step: Quantifiers and Assertions

### Quantifier Types

#### 1. Collapsing Quantifiers (used as criteria)

| Quantifier | Meaning | Empty Axis |
|------------|---------|------------|
| `"all"` | All elements must match | True (vacuous) |
| `"some"` | At least one must match | False |
| `"none"` | No elements may match | True (vacuous) |
| `"exists"` | Axis must have elements | False |

#### 2. Non-Collapsing Quantifiers (defines filter axis)

| Quantifier | Meaning | Behavior |
|------------|---------|----------|
| `"for-each"` | Evaluate each element | Preserves axis, marks truth values |

### Pattern Examples

#### Example 1: Simple Global Check
```json
{
  "assertion_condition": {
    "quantifiers": {
      "paragraph": "some"
    },
    "condition": true
  }
}
```
**Result**: Single boolean - "Do SOME paragraphs contain true?"

#### Example 2: Hierarchical Filtering (RECOMMENDED)
```json
{
  "assertion_condition": {
    "quantifiers": {
      "document": "for-each",  // Which documents to evaluate
      "paragraph": "some"      // Criterion: document must have SOME matching paragraph
    },
    "condition": true
  }
}
```
**Result**: Truth mask along document axis - `['%{truth value}(true)', '%{truth value}(false)', ...]`

**Interpretation**: 
- For each document, check if SOME paragraph is true
- Documents that pass become `%{truth value}(true)`
- Documents that fail become `%{truth value}(false)`

#### Example 3: Stricter Criterion
```json
{
  "assertion_condition": {
    "quantifiers": {
      "document": "for-each",  // Which documents
      "paragraph": "all"       // ALL paragraphs must match
    },
    "condition": true
  }
}
```
**Result**: Only documents where ALL paragraphs are true get `%{truth value}(true)`

## Truth Mask Output

### What is a Truth Mask?

The TIA step produces a **truth mask** - a reference with the same structure as the input, but with truth value markers:

```python
# Input (from TVA):
[[True, True, True],   # document 0
 [True, False, True],  # document 1
 [True, True, True]]   # document 2

# With "for-each document where ALL paragraphs":
# Output (from TIA):
['%{truth value}(true)',   # doc 0: all True
 '%{truth value}(false)',  # doc 1: has False
 '%{truth value}(true)']   # doc 2: all True
```

### Using the Truth Mask Downstream

The truth mask can be used for filtering in subsequent inferences:

```python
# In downstream IR step:
truth_mask = get_reference_from_previous_judgement()

# Filter data using element_action:
filtered_data = element_action(
    lambda value, mask: value if mask == "%{truth value}(true)" else SKIP,
    [data_reference, truth_mask]
)
```

## States Output

After TIA completes, the states object contains:

```python
states.condition_met: bool  
# Overall boolean: did ANY element pass the criteria?
# Used by timing operators (@if) for control flow

states.primary_filter_axis: Optional[str]
# The name of the filter axis (from "for-each" quantifier)
# Helps downstream know which axis was evaluated

# The truth mask itself is in:
states.get_reference("inference", "TIA")
```

## Advanced: Multi-Axis Assertions

### 3-Axis Example

```json
{
  "assertion_condition": {
    "quantifiers": {
      "section": "for-each",   // Filter: which sections
      "document": "some",      // Criterion: section must have SOME passing document
      "paragraph": "all"       // Sub-criterion: document passes if ALL paragraphs match
    },
    "condition": true
  }
}
```

**Processing**:
1. For each section:
   - For each document in that section:
     - Check if ALL paragraphs are true
   - Check if SOME document passed
2. Produce truth mask along section axis

## Comparison with Other Sequences

| Sequence | Has TIA? | Output Type | Use Case |
|----------|----------|-------------|----------|
| `imperative_in_composition` | No | Direct result | Actions, transformations |
| `judgement_in_composition` | **Yes** | Truth mask | Evaluations, filtering |
| Legacy `judgement` | Partial | Boolean | Simple checks |

## Complete Example

```json
{
  "paradigm": "document_relevance_scorer",
  "value_order": {
    "documents": 0,
    "query": 1
  },
  "assertion_condition": {
    "quantifiers": {
      "document": "for-each",
      "paragraph": "some"
    },
    "condition": true
  }
}
```

**What happens:**
1. IWI loads the `document_relevance_scorer` paradigm and stores the assertion
2. MFP composes a function that scores document-paragraph pairs for relevance
3. TVA executes scoring → produces boolean tensor `[document, paragraph]`
4. **TIA applies hierarchical assertion**:
   - For each document, checks if SOME paragraph is relevant
   - Produces truth mask: `['%{truth value}(true)', ...]` per document
5. OR outputs the truth mask for downstream filtering

This enables patterns like: "Continue processing only documents that have at least one relevant paragraph."

---

## Integration with Timing and Filter Injection

### How Judgement + Timing Work Together

When a judgement with `for-each` quantifier is used as a condition for `@if` or `@if!` timing, the truth mask is automatically **injected as a filter** for the parent inference.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Judgement Inference (e.g., <doc is relevant>)                │
│    - TIA produces truth mask: [true, false, true, false]        │
│    - Stored on blackboard via orchestrator                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Timing Inference (@if(<doc is relevant>))                    │
│    - Checks condition → passes (condition_met = True)           │
│    - Retrieves truth mask from blackboard                       │
│    - Injects filter into workspace for parent inference         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Parent Inference (the timed action)                          │
│    - IR step can read injected filter from workspace            │
│    - Apply filter to input references: false → @#SKIP#@         │
│    - Process only elements that passed the judgement            │
└─────────────────────────────────────────────────────────────────┘
```

### Workspace Filter Format

When timing injects a filter, it's stored in the workspace as:

```python
workspace["__filter__{parent_flow_index}"] = [
    {
        'truth_mask': {
            'tensor': ['%{truth value}(true)', '%{truth value}(false)', ...],
            'axes': ['document'],
            'filter_axis': 'document',
            'shape': (4,)
        },
        'condition': '<doc is relevant>',
        'source_flow_index': '1.1.3.1'
    },
    # Additional filters for nested @if (AND semantics)
]
```

### Multiple Filters (Nested @if)

When you have nested timing conditions:

```ncd
<= ::(process documents) | 1.1. imperative
    <= @if(<doc is relevant>) | 1.1.1. timing
        <= @if(<doc is recent>)  | 1.1.1.1. timing
```

Both filters are accumulated with **AND semantics**:
- `workspace["__filter__1.1"]` contains both filters
- IR step should apply all filters: element must pass ALL to be kept

### Binary Branching (Backward Compatible)

The existing `@if`/`@if!` binary behavior is preserved:

| `condition_met` | `@if` | `@if!` |
|-----------------|-------|--------|
| `True` (some elements passed) | Execute + Inject Filter | Skip |
| `False` (no elements passed) | Skip | Execute (no filter to inject) |

When **all elements fail** (`condition_met = False`), the entire parent inference is skipped - no filter injection needed.

### Example NormCode

```ncd
# Step 1: Judgement evaluates relevance per document
<- <doc is relevant> | 1.1. judgement_in_composition
    <= :%(True):<{doc}<$({document})%_> mentions keyword>
        assertion_condition: {
            "quantifiers": {"document": "for-each"},
            "condition": True
        }
    <- [documents]

# Step 2: Timing gates the action with filter injection
<- {processed docs} | 1.2. imperative
    <= ::(summarize documents) | 1.2.1. timing
        <= @if(<doc is relevant>)
    <- [documents]
```

**Execution Flow:**
1. Judgement produces: `[true, false, true, false]` for 4 documents
2. `condition_met = True` (some docs are relevant)
3. Timing passes, injects filter into `workspace["__filter__1.2"]`
4. Imperative's IR step can apply filter to `[documents]`
5. Only `doc1` and `doc3` are processed (others become `@#SKIP#@`)

### Applying Filters in IR (For Custom Sequences)

To consume injected filters in an IR step:

```python
def input_references(inference: Inference, states: States) -> States:
    # Check for injected filter
    filter_key = f"__filter__{states.flow_index}"
    filters = states.workspace.get(filter_key)
    
    if filters:
        for vc in inference.value_concepts:
            if not vc.reference:
                continue
            
            for filter_data in filters:
                filter_axis = filter_data['truth_mask']['filter_axis']
                truth_mask_tensor = filter_data['truth_mask']['tensor']
                
                # Apply filter if reference has the filter axis
                if filter_axis in vc.reference.axes:
                    vc.reference = _apply_truth_mask(vc.reference, truth_mask_tensor)
        
        # Cleanup
        del states.workspace[filter_key]
    
    # ... rest of IR logic
```

### Key Points

1. **Automatic Storage**: Orchestrator stores truth mask on blackboard after judgement completes
2. **Automatic Injection**: Timing step injects filter when `@if`/`@if!` passes
3. **AND Semantics**: Multiple nested conditions accumulate as AND
4. **Backward Compatible**: No changes needed for existing binary branching
5. **IR Consumption**: Deferred - sequences can implement filter application in their IR steps