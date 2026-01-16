# Timing Sequence

## Overview

The **Timing Sequence** is a syntactic agent sequence that controls **execution flow**—determining **when** an inference runs and **whether** it should be skipped based on conditions. It is the **traffic control system** of NormCode plans, enabling conditional branching and dependency sequencing.

**Sequence Pattern**: `(IWI → T → OWI)`

**Associated NormCode Operators**: 
- `@.` (After / `@after`) - Sequencing: "Run after X completes"
- `@:'` (If / `@if`) - Conditional: "Run if X is true"
- `@:!` (If Not / `@if!`) - Negated Conditional: "Run if X is false"

**Key Characteristics**:
- ✅ **Deterministic** (no LLM calls)
- ✅ **Free** (no token cost)
- ✅ **Stateless** (queries the Blackboard, doesn't modify references)
- ✅ **Gating** (controls whether parent inference executes or skips)

---

## When to Use Timing

Timing is essential when you need to:

| Use Case | Operator | Example |
|----------|----------|---------|
| Ensure execution order | `@.` | "Calculate remainder after sum is computed" |
| Skip work if condition fails | `@:'` | "Only save result if validation passed" |
| Handle edge cases | `@:!` | "Continue loop only if NOT all numbers are zero" |
| Prevent race conditions | `@.` | "Wait for data to be loaded before processing" |
| Implement early termination | `@:!` | "Stop iteration when termination condition met" |
| Filter elements in parent | `@:'` + truth mask | "Only process documents marked as relevant" |

**Timing is NOT for**:
- Data manipulation (use Assigning or Grouping)
- Iteration (use Looping)
- LLM reasoning (use Imperative or Judgement)

---

## The Three-Step Pipeline

### Step 1: IWI (Input Working Interpretation)

**File**: `_iwi.py`

**Purpose**: Initialize the states container with syntax configuration and orchestrator context.

**Key Operations**:
- Extract `marker` (`"after"`, `"if"`, or `"if!"`)
- Extract `condition` (the concept name to check)
- Load `blackboard` reference (for querying concept statuses)
- Load `workspace` (for filter injection)
- Load `flow_index` (for parent inference identification)

**State Updates**:
```python
states.syntax.marker = "after" | "if" | "if!"
states.syntax.condition = "{concept_name}" | "<proposition>"
states.blackboard = <Blackboard instance>
states.workspace = {...}  # Shared workspace for filter injection
states.flow_index = "X.Y.Z"  # This timing inference's flow index
```

**Critical Note**: The timing sequence **requires the Blackboard** to function. Without it, the sequence will raise an error.

---

### Step 2: T (Timing)

**File**: `_t.py`

**Purpose**: Execute the core timing logic by querying the Blackboard and setting readiness flags.

**Algorithm**:

1. **Initialize Timer**: Create a `Timer` instance with the Blackboard
2. **Check condition based on marker**:
   - `@after`: Check if condition concept is complete
   - `@if`: Check if condition is complete AND evaluate its truth
   - `@if!`: Check if condition is complete AND evaluate its negation
3. **Set readiness flags**:
   - `states.timing_ready`: Is the parent inference ready to run?
   - `states.to_be_skipped`: Should the parent inference be skipped?
4. **Inject filters** (if applicable): If condition passes and has a truth mask, inject filter into workspace

**State Updates**:
```python
states.timing_ready = True | False  # Can parent proceed?
states.to_be_skipped = True | False  # Should parent skip?
states.workspace[f"__filter__{parent_flow_index}"] = [...]  # Optional filter injection
```

**The Decision Matrix**:

| Marker | Condition Status | Condition Detail | `timing_ready` | `to_be_skipped` | Action |
|--------|------------------|------------------|----------------|-----------------|--------|
| `@after` | `complete` | Any | `True` | `False` | Proceed |
| `@after` | Not complete | N/A | `False` | `False` | Wait |
| `@if` | `complete` | `success` / `None` | `True` | `False` | Proceed |
| `@if` | `complete` | `condition_not_met` | `True` | `True` | Skip |
| `@if` | Not complete | N/A | `False` | `False` | Wait |
| `@if!` | `complete` | `condition_not_met` | `True` | `False` | Proceed |
| `@if!` | `complete` | `success` / `None` | `True` | `True` | Skip |
| `@if!` | Not complete | N/A | `False` | `False` | Wait |

---

### Step 3: OWI (Output Working Interpretation)

**File**: `_owi.py`

**Purpose**: Finalization step (currently a no-op for syntactic sequences).

**Key Operations**:
- Mark the step as complete
- Log completion

---

## The Three Timing Modes

### Mode 1: `@.` (After / Sequencing)

**Intuition**: Like a **yield sign**. Wait for dependency to complete, then proceed.

**Implementation**: `Timer.check_progress_condition()`

**Behavior**:
1. Query Blackboard: Is `condition` concept complete?
2. If **yes**: Set `timing_ready = True` (parent can run)
3. If **no**: Set `timing_ready = False` (parent waits)

**Example**:

```ncd
{remainder}
    <= ::(get the {1}?<$({remainder})%> of {2}<$({digit sum})%> divided by 10)
        <= @. ({digit sum})
    <- {remainder}?<:{1}>
    <- {digit sum}<:{2}>
```

**Explanation**:
- The `@.` timing inference waits until `{digit sum}` is complete
- Once complete, the parent imperative inference can execute
- This ensures the remainder is only calculated **after** the sum is available

**Use Cases**:
- Enforce execution order (A must complete before B starts)
- Prevent race conditions (data must be loaded before processing)
- Chain operations (output of step 1 is input to step 2)

**Key Point**: `@after` **never skips**. It only controls **when** the parent runs, not **whether** it runs.

---

### Mode 2: `@:'` (If / Conditional Execution)

**Intuition**: Like a **green light**. Proceed only if condition is true.

**Implementation**: `Timer.check_if_condition()`

**Behavior**:
1. Query Blackboard: Is `condition` concept complete?
2. If **not complete**: Set `timing_ready = False` (wait)
3. If **complete**:
   - Check completion detail:
     - `success` / `None`: Set `timing_ready = True`, `to_be_skipped = False` (proceed)
     - `condition_not_met`: Set `timing_ready = True`, `to_be_skipped = True` (skip)
   - If proceeding and condition has truth mask: Inject filter into workspace

**Example**:

```ncd
{number pair}<$={1}>
    <= $+({number pair to append}:{number pair})%:[{number pair}]
        <= @:! (<all number is 0>)
            <= @:' (<carry-over number is 0>)
    <- {number pair to append}<$={1}>
    <- <all number is 0>
    <- <carry-over number is 0>
```

**Explanation**:
- The nested `@:' (<carry-over number is 0>)` checks if carry is zero
- If carry is **not zero**, the parent `$+` (append) is **skipped**
- This implements conditional accumulation in the addition loop

**Use Cases**:
- Skip work based on conditions (validation, eligibility checks)
- Implement early termination (loop exit conditions)
- Conditional branching (different paths based on state)
- Filter processing (only handle elements that match criteria)

**Truth Mask Filter Injection**:

When a `@if` condition:
1. Passes (condition is true)
2. Has a truth mask (from a judgement with for-each quantifier)

The timing step **injects a filter** into the workspace:

```python
states.workspace[f"__filter__{parent_flow_index}"] = [
    {
        'truth_mask': {'tensor': [...], 'axes': [...], 'filter_axis': '...'},
        'condition': '<doc is relevant>',
        'source_flow_index': '1.2.3.1'
    }
]
```

The parent inference's **IR step** can then apply this filter to all input references, processing only elements where the condition was true.

---

### Mode 3: `@:!` (If Not / Negated Conditional)

**Intuition**: Like a **red light bypass**. Proceed only if condition is false.

**Implementation**: `Timer.check_if_not_condition()`

**Behavior**:
1. Query Blackboard: Is `condition` concept complete?
2. If **not complete**: Set `timing_ready = False` (wait)
3. If **complete**:
   - Check completion detail:
     - `condition_not_met`: Set `timing_ready = True`, `to_be_skipped = False` (proceed)
     - `success` / `None`: Set `timing_ready = True`, `to_be_skipped = True` (skip)
   - If proceeding: Inject filter (note: inverted semantics already applied in skip decision)

**Example**:

```ncd
{number pair}<$={1}>
    <= $+({number pair to append}:{number pair})%:[{number pair}]
        <= @:! (<all number is 0>)
    <- {number pair to append}<$={1}>
    <- <all number is 0>
```

**Explanation**:
- The `@:!` checks if **NOT** all numbers are zero
- If all numbers **are zero**, the append is **skipped** (loop terminates)
- This implements the loop continuation condition

**Use Cases**:
- Loop continuation (continue **until** condition becomes true)
- Inverse logic (proceed when something is **absent**)
- Edge case handling (skip when abnormal condition detected)

**Key Difference from `@if`**:
- `@if`: "Do this **if** condition is true"
- `@if!`: "Do this **unless** condition is true"

---

## The Timer Class (`infra/_syntax/_timer.py`)

The actual timing logic is implemented in the **`Timer`** class, which provides stateless query methods over the Blackboard:

### Core Methods

#### `check_progress_condition(condition: str) -> bool`

**Purpose**: Check if a concept is complete (for `@after`).

**Parameters**:
- `condition`: The concept name to check

**Returns**: 
- `True` if concept status is `'complete'`
- `False` otherwise

**Implementation**:
```python
def check_progress_condition(self, condition: str) -> bool:
    return self.blackboard.check_progress_condition(condition)
```

**Blackboard Query**:
- Resolves concept aliases (if using `$=` identity)
- Returns `True` if `concept_status == 'complete'`

---

#### `check_if_condition(condition: str) -> tuple[bool, bool]`

**Purpose**: Check an `@if` condition, returning readiness and skip decision.

**Parameters**:
- `condition`: The concept name to check

**Returns**: 
- Tuple `(is_ready, to_be_skipped)`
  - `is_ready`: Can parent proceed? (False = wait)
  - `to_be_skipped`: Should parent skip? (True = skip)

**Decision Logic**:

```python
if concept_status != 'complete':
    return (False, False)  # Wait

detail = blackboard.get_completion_detail_for_concept(condition)

if detail == 'condition_not_met':
    return (True, True)  # Ready, but skip
elif detail in ['success', None]:
    return (True, False)  # Ready, proceed
```

**Completion Details**:
- `'success'`: Concept completed successfully (condition is true)
- `'condition_not_met'`: Judgement evaluated to false
- `None`: Non-judgement concept (treated as success)

---

#### `check_if_not_condition(condition: str) -> tuple[bool, bool]`

**Purpose**: Check an `@if!` condition (inverse logic).

**Parameters**:
- `condition`: The concept name to check

**Returns**: 
- Tuple `(is_ready, to_be_skipped)`

**Decision Logic** (inverted from `@if`):

```python
if concept_status != 'complete':
    return (False, False)  # Wait

detail = blackboard.get_completion_detail_for_concept(condition)

if detail == 'condition_not_met':
    return (True, False)  # Ready, proceed (condition is false)
elif detail in ['success', None]:
    return (True, True)  # Ready, skip (condition is true)
```

---

#### `get_truth_mask_for_filter(condition: str) -> Optional[Dict[str, Any]]`

**Purpose**: Retrieve truth mask from a judgement condition for filter injection.

**Parameters**:
- `condition`: The judgement concept name (e.g., `'<doc is relevant>'`)

**Returns**: 
- Truth mask data dict containing:
  - `'tensor'`: List of truth values (e.g., `['%{truth value}(true)', '%{truth value}(false)', ...]`)
  - `'axes'`: List of axis names
  - `'filter_axis'`: The primary filter axis (from for-each quantifier)
- `None` if no truth mask is available

**Use Case**:

When a judgement uses a for-each quantifier:

```ncd
<doc is relevant>
    <= :%(for-each):<{1}<$({doc})%> is relevant to {2}<$({query})%>>
    <- [all docs]<:{1}>
    <- {query}<:{2}>
```

The judgement produces a truth mask: `[true, false, true, ...]` along the `doc` axis.

If `@if(<doc is relevant>)` **passes**, the timing step injects this mask, allowing the parent inference to **process only relevant docs**.

---

## Filter Injection Mechanism

One of the most powerful features of the timing sequence is its ability to **inject filters** into the parent inference's execution context.

### How It Works

1. **Judgement with For-Each**: A judgement uses a for-each quantifier to evaluate a condition across a collection:

   ```ncd
   <doc is relevant>
       <= :%(for-each):<{doc} matches criteria>
       <- [all docs]
   ```

2. **Truth Mask Created**: The judgement produces a truth mask stored in the Blackboard:

   ```python
   blackboard.set_truth_mask('<doc is relevant>', {
       'tensor': ['%{truth value}(true)', '%{truth value}(false)', '%{truth value}(true)'],
       'axes': ['doc'],
       'filter_axis': 'doc'
   })
   ```

3. **Timing Condition Passes**: An `@if` or `@if!` timing inference evaluates the condition:

   ```ncd
   {processed docs}
       <= ::(process {docs})
           <= @:' (<doc is relevant>)
       <- [all docs]
   ```

4. **Filter Injected**: If condition passes, the timing step injects the filter:

   ```python
   # In _t.py:
   _inject_filter_for_parent(states, timer, condition)
   
   # Result in workspace:
   states.workspace['__filter__1.2.3'] = [
       {
           'truth_mask': {...},
           'condition': '<doc is relevant>',
           'source_flow_index': '1.2.3.1'
       }
   ]
   ```

5. **Parent IR Applies Filter**: The parent inference's IR step reads the filter and applies it to all input references:

   ```python
   # In parent's _ir.py (via apply_injected_filters):
   filter_key = f"__filter__{inference.flow_index}"
   filters = workspace.get(filter_key, [])
   
   for filter_spec in filters:
       truth_mask = filter_spec['truth_mask']
       # Apply truth mask to all references, keeping only 'true' elements
   ```

6. **Parent Processes Filtered Data**: The parent inference now operates only on filtered elements:

   ```
   Original: [doc1, doc2, doc3]
   Truth Mask: [true, false, true]
   Filtered: [doc1, doc3]  ← Parent sees only these
   ```

### Filter Accumulation (Nested `@if`)

Filters **accumulate** when multiple `@if` conditions are nested:

```ncd
{result}
    <= ::(process {items})
        <= @:' (<condition A>)
            <= @:' (<condition B>)
    <- [items]
```

Both filters are injected and applied (AND semantics):

```python
workspace['__filter__1.2.3'] = [
    {'condition': '<condition A>', 'truth_mask': {...}},
    {'condition': '<condition B>', 'truth_mask': {...}}
]
```

The parent's IR step applies **both** filters sequentially, keeping only elements where **all** conditions are true.

---

## Real-World Example: Base-X Addition Loop Termination

From the NormCode base-X addition algorithm, timing is used to implement loop termination:

```ncd
{number pair}<$={1}> | 1.1.3
    <= $+({number pair to append}:{number pair})%:[{number pair}]
        <= @if!(<all number is 0>) | 1.1.3.1
            <= @if(<carry-over number is 0>) | 1.1.3.1.1
    <- {number pair to append}<$={1}>
    <- <all number is 0> | 1.1.3.3
    <- <carry-over number is 0> | 1.1.3.4
```

**What happens**:

1. **Outer Loop**: `*every({number pair})` iterates, processing digits
2. **Append Operation**: `$+({number pair to append})` adds new number pair to collection
3. **Nested Timing**:
   - **`@if!(<all number is 0>)` at 1.1.3.1**: Check if NOT all numbers are zero
   - **`@if(<carry-over number is 0>)` at 1.1.3.1.1**: Check if carry is zero

**Decision Tree**:

```
Is <all number is 0> complete?
└─ No → Wait (both timing inferences stay pending)
└─ Yes → Check detail
    └─ All zero?
        └─ Yes → @if! proceeds, skip 1.1.3.1.1 → Skip entire append → Loop terminates
        └─ No → @if! proceeds, check carry
            └─ Is <carry-over number is 0> complete?
                └─ No → Wait
                └─ Yes → Check detail
                    └─ Carry is zero?
                        └─ Yes → @if proceeds → Execute append → Loop continues
                        └─ No → @if skips append → Process carry first, then retry
```

**Key Insight**: The nested `@if!` + `@if` structure implements complex conditional logic **without LLM reasoning**, purely through timing gates.

---

## Flow Index Hierarchy and Parent Identification

The timing sequence uses flow indices to determine which inference it controls:

**Flow Index Structure**:
```
1.2.3       ← Parent inference
1.2.3.1     ← Timing inference (controls 1.2.3)
1.2.3.1.1   ← Nested timing (controls 1.2.3.1)
```

**Parent Calculation** (`_get_parent_flow_index`):
```python
def _get_parent_flow_index(flow_index: str) -> str:
    # '1.2.3.1' → '1.2.3'
    parts = flow_index.split('.')
    return '.'.join(parts[:-1])
```

**Why This Matters**:

1. **Filter Targeting**: Filters are injected with the parent's flow index as the key
2. **Orchestrator Coordination**: The orchestrator checks `timing_ready` and `to_be_skipped` flags to decide parent's fate
3. **Nested Timing**: A timing inference can itself have timing children (nested conditions)

---

## Interaction with the Blackboard

The timing sequence is **read-only** with respect to the Blackboard—it queries state but doesn't modify it.

### Blackboard Methods Used

#### `get_concept_status(concept_name: str) -> str`

Returns the status of a concept: `'empty'`, `'pending'`, `'in_progress'`, `'complete'`

- Automatically resolves concept aliases (for `$=` identity)
- Used to check if a condition is ready to evaluate

---

#### `check_progress_condition(concept_name: str) -> bool`

Convenience method that returns `True` if concept status is `'complete'`.

- Used by `@after` timing
- Resolves aliases internally

---

#### `get_completion_detail_for_concept(concept_name: str) -> Optional[str]`

Returns the completion detail for the inference that produced the concept:
- `'success'`: Normal completion
- `'condition_not_met'`: Judgement evaluated to false
- `'skipped'`: Inference was skipped by timing
- `None`: No detail available

Used by `@if` and `@if!` to distinguish between "condition true" and "condition false".

---

#### `get_truth_mask(concept_name: str) -> Optional[Dict[str, Any]]`

Retrieves the truth mask for a judgement concept (if available).

- Used for filter injection
- Returns `None` if concept doesn't have a truth mask

---

#### `resolve_concept_name(concept_name: str) -> str`

Resolves concept aliases through the identity chain.

- If `{A} $= {B}`, both names resolve to the same canonical concept
- Ensures timing checks work correctly with aliased concepts

---

## Syntax Extraction

The timing sequence expects the following structure in `working_interpretation`:

```python
{
    "syntax": {
        "marker": "after" | "if" | "if!",
        "condition": "{concept_name}" | "<proposition>"
    },
    "blackboard": <Blackboard instance>,  # From orchestrator
    "workspace": {...},  # Shared workspace for filter injection
    "flow_info": {
        "flow_index": "X.Y.Z"
    }
}
```

### NormCode Syntax Mapping

| Old Syntax | New Syntax | Marker | Description |
|------------|------------|--------|-------------|
| `@after({dep})` | `@. ({dep})` | `"after"` | Wait for dependency |
| `@if(<cond>)` | `@:' (<cond>)` | `"if"` | Proceed if true |
| `@if!(<cond>)` | `@:! (<cond>)` | `"if!"` | Proceed if false |

---

## Configuration in AgentFrame

The timing sequence is registered and configured in the AgentFrame:

**Setup** (`set_up_timing_demo`):
- Registers the `timing` sequence decorator
- Defines the 3-step pipeline: `(IWI-T-OWI)`

**Configuration** (`configure_timing_demo`):
- Maps each step name to its implementation method
- Methods come from the `timing_methods` dict in `__init__.py`

**Invocation**:
```python
from infra._agent._steps.timing import timing_methods

agent_frame.configure_inference(
    inference_instance,
    sequence="timing",
    methods=timing_methods
)
```

---

## Key Design Principles

### 1. Stateless Queries

The timing sequence **never modifies** the Blackboard or concept references. It only:
- Queries concept statuses
- Retrieves completion details
- Reads truth masks

This makes timing:
- **Predictable**: Same Blackboard state → same timing decision
- **Cacheable**: Results could be memoized (though currently not)
- **Debuggable**: No hidden side effects

---

### 2. Workspace-Based Filter Injection

Rather than modifying references directly, timing injects filters into the **shared workspace**.

**Why?**
- **Separation of concerns**: Timing decides "what to filter", IR applies "how to filter"
- **Accumulation**: Multiple nested `@if` conditions can contribute filters
- **Transparency**: Filters are logged and inspectable

---

### 3. Blackboard as Source of Truth

The timing sequence delegates all state queries to the Blackboard:
- Concept statuses
- Completion details
- Truth masks
- Concept aliases

**Why?**
- **Single source of truth**: No duplicate state tracking
- **Orchestrator consistency**: Timing sees exactly what orchestrator sees
- **Checkpointing**: Blackboard state is serialized, timing decisions are reproducible

---

### 4. Two-Phase Decision (Ready + Skip)

Timing returns **two flags**, not one:

1. **`timing_ready`**: Is the condition **evaluated**?
   - `False` → Parent waits (condition not complete yet)
   - `True` → Parent can proceed to execution phase

2. **`to_be_skipped`**: Should parent **skip execution**?
   - `False` → Parent executes normally
   - `True` → Parent skips (marks as completed with detail `'skipped'`)

**Why separate?**

This allows the orchestrator to distinguish:
- **Waiting** (not ready) vs. **Skipping** (ready but no-op)
- **Pending** (might run later) vs. **Never** (will never run this cycle)

---

### 5. Subject-Agnostic

Like other syntactic sequences, timing doesn't require a specific "Body" or Subject (`:S:`). It operates on the **control flow structure**, not data content.

This universality means:
- Timing works identically across all AgentFrames
- No tool invocation required
- No paradigm configuration needed

---

## Orchestrator Integration

The timing sequence coordinates tightly with the orchestrator:

### Orchestrator's Responsibility

1. **Provide Blackboard**: Pass the Blackboard instance to timing's working interpretation
2. **Provide Workspace**: Pass a shared workspace dict for filter injection
3. **Check Readiness**: Query `states.timing_ready` after timing execution
4. **Handle Skip**: If `states.to_be_skipped`, mark parent as `'completed'` with detail `'skipped'`
5. **Propagate Filters**: Ensure parent's IR step has access to workspace filters

### Timing Sequence's Responsibility

1. **Query Blackboard**: Check concept statuses and completion details
2. **Set Flags**: Update `timing_ready` and `to_be_skipped` based on logic
3. **Inject Filters**: If condition passes and has truth mask, add filter to workspace
4. **Log Decisions**: Provide clear logging for debugging

---

## Troubleshooting

### Problem: Timing inference never becomes ready

**Cause**: Condition concept is stuck in `'pending'` or `'in_progress'` state

**Solution**: 
- Check that the condition inference is actually executing
- Verify no circular dependencies (A waits for B, B waits for A)
- Check orchestrator logs for errors in condition inference

---

### Problem: `@if` skips when it shouldn't

**Cause**: Condition concept completed with detail `'condition_not_met'`

**Solution**:
- Verify the judgement logic is correct
- Check judgement inputs—are they what you expect?
- Use `@if!` if you want inverted logic

---

### Problem: Filter not applied to parent inference

**Cause**: Filter injection failed or parent's IR doesn't support filtering

**Solution**:
- Check that parent's IR step calls `apply_injected_filters()`
- Verify timing inference has correct flow_index
- Check workspace is shared between timing and parent
- Ensure judgement produced a truth mask (for-each quantifier required)

---

### Problem: Nested `@if` conditions behave unexpectedly

**Cause**: Filter accumulation (AND semantics) may not match intent

**Solution**:
- Remember that multiple `@if` conditions are **ANDed** (all must pass)
- If you want OR logic, restructure using separate branches
- Check filter injection logs to see which filters are active

---

### Problem: "Blackboard not found" error

**Cause**: Orchestrator didn't pass Blackboard to working interpretation

**Solution**:
- Ensure orchestrator includes `blackboard` in working interpretation
- Verify AgentFrame setup is correct
- Check that timing sequence is being invoked properly

---

## Testing Checklist

When implementing or modifying timing, verify:

- [ ] IWI extracts `marker` and `condition` correctly
- [ ] IWI loads `blackboard`, `workspace`, and `flow_index`
- [ ] T step queries Blackboard (doesn't mutate it)
- [ ] `@after` waits until condition is complete
- [ ] `@after` never skips (only gates timing)
- [ ] `@if` proceeds when condition is true, skips when false
- [ ] `@if!` proceeds when condition is false, skips when true
- [ ] `@if` waits if condition is not complete yet
- [ ] Filter injection works for judgements with truth masks
- [ ] Nested `@if` conditions accumulate filters correctly
- [ ] Parent flow index is calculated correctly
- [ ] Concept aliases are resolved correctly
- [ ] Logging provides clear debugging info at each decision point

---

## Comparison: Timing vs. Other Sequences

| Aspect | Timing | Grouping | Assigning | Looping |
|--------|--------|----------|-----------|---------|
| **Purpose** | Control flow | Combine data | Select/update data | Iterate collections |
| **Queries Blackboard?** | ✅ Yes | ❌ No | ❌ No | ✅ Yes (for workspace) |
| **Modifies References?** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Can Skip Parent?** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Stateless?** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No (workspace) |
| **Step Count** | 3 | 5 | 5 | 5 |

---

## Related Documentation

- **NormCode Formalism**: See `context_store/shared---normcode_formalism_basic.md` (Section 3.2.2)
- **Agent Sequences Guide**: See `context_store/shared---normcode_agent_sequence_guide.md` (Section 3.3)
- **Syntactic Operators**: See `context_store/shared---normcode_syntatical_concepts_reconstruction.md` (Section 3.4)
- **Blackboard**: See `infra/_orchest/_blackboard.py`
- **Orchestrator**: See orchestrator documentation for integration details

---

## Summary

The Timing Sequence is the **traffic control system** of NormCode plans:

✅ Controls **when** inferences execute (sequencing with `@after`)  
✅ Controls **whether** inferences execute (branching with `@if`/`@if!`)  
✅ Operates deterministically (no LLM calls, free, fast)  
✅ Queries Blackboard (stateless, read-only)  
✅ Injects filters for parent inferences (via truth masks)  
✅ Supports nested conditions (filter accumulation with AND semantics)  

**Mental Model**: Think of timing as **yield signs and traffic lights** for your plan:
- `@after` = "Wait for the car ahead to pass"
- `@if` = "Proceed if light is green, wait at intersection if red"
- `@if!` = "Proceed if light is red (special bypass lane)"

**When in doubt**: 
- Use `@after` when you need **execution order** (A before B)
- Use `@if` when you need **conditional execution** (only if X)
- Use `@if!` when you need **inverse logic** (only if NOT X)

