# Looping Sequence

The **looping sequence** (formerly "quantifying") is a syntactic agent sequence that enables iteration over collections with stateful carry-over between iterations. It is the execution engine behind the `*every` operator in NormCode.

---

## Purpose

The looping sequence allows NormCode plans to:
- **Iterate** over collections element-by-element
- **Carry state** between iterations (e.g., running totals, carry-over digits)
- **Track progress** through a persistent workspace
- **Aggregate results** across all iterations
- **Support nested loops** via indexed workspaces

This is a **syntactic** (not semantic) sequence—it manipulates data structure without invoking LLM reasoning.

---

## The Six-Step Pipeline

The looping sequence follows a standardized pipeline:

```
IWI → IR → GR → LR → OR → OWI
```

| Step | Name | Purpose |
|------|------|---------|
| **IWI** | Input Working Interpretation | Parse syntax config, initialize workspace |
| **IR** | Input References | Load concept references from the inference |
| **GR** | Grouping References | Flatten the collection to be looped over |
| **LR** | Looping References | Core loop logic: retrieve next element, update workspace, aggregate results |
| **OR** | Output Reference | Finalize output and propagate context |
| **OWI** | Output Working Interpretation | Check completion status |

---

## How It Works

### High-Level Flow

1. **GR Step**: Takes the base collection (e.g., `[{number pair}]`) and flattens it into a list of elements to loop over
2. **LR Step**: 
   - Retrieves the next unprocessed element
   - Checks if the current iteration produced a new result
   - Stores results and carried state in the workspace
   - Aggregates all completed iterations into a combined reference
3. **OWI Step**: Checks if all elements have been processed; if not, the orchestrator re-runs the loop body

### The Workspace

The looping sequence maintains a **workspace** (a nested dictionary) that persists across iterations:

```python
workspace = {
    "1_{number pair}": {  # Loop index 1, concept "{number pair}"
        0: {  # First iteration
            "{number pair}": Reference(...),      # The base element
            "{result}": Reference(...),           # The inferred concept
            "{carry-over}*1": Reference(...)      # Carried state
        },
        1: {  # Second iteration
            "{number pair}": Reference(...),
            "{result}": Reference(...),
            "{carry-over}*1": Reference(...)
        },
        ...
    }
}
```

**Key Insight**: The workspace allows the looper to "remember" which elements have been processed and what state should be carried forward.

---

## Working Interpretation Syntax

The looping sequence expects a `working_interpretation` with the following structure:

```python
{
    "syntax": {
        "marker": "every",                        # The loop operator
        "loop_index": 1,                          # Loop nesting level (1 = outermost)
        "LoopBaseConcept": "{number pair}",       # The collection to iterate over
        "CurrentLoopBaseConcept": "{number pair}*1",  # Current element name (optional)
        "group_base": "{number pair}",            # Axis for grouping
        "ConceptToInfer": ["{result}"],           # What each iteration produces
        "InLoopConcept": {                        # State to carry between iterations
            "{carry-over}*1": 1                   # Old format: concept_name -> carry_index
            # OR new format:
            # "{carry-over}": {
            #     "current_name": "{carry-over}*1",
            #     "carry_over": 1
            # }
        }
    },
    "workspace": {},  # Persistent workspace dict
    "flow_info": {
        "flow_index": "1.2.3"
    }
}
```

### Key Fields

| Field | Description | Example |
|-------|-------------|---------|
| `loop_index` | Nesting level (1 = outermost, 2 = nested, etc.) | `1` |
| `LoopBaseConcept` | The collection to iterate over | `"{number pair}"` |
| `CurrentLoopBaseConcept` | Name for current element (defaults to `LoopBaseConcept + "*"`) | `"{number pair}*1"` |
| `ConceptToInfer` | What gets computed each iteration | `["{digit sum}"]` |
| `InLoopConcept` | State carried forward | `{"{carry}*1": 1}` |
| `group_base` | Axis to flatten during grouping | `"{number pair}"` |

---

## Example: Base-X Addition with Carry-Over

This example shows a loop that processes number pairs, carrying a `{carry-over}` between iterations:

### NormCode Syntax

```ncd
{new number pair} | 1. looping
    <= *every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]
    
    <- {digit sum} | 1.1.2. imperative
        <= ::(sum {1} and {2} to get {3})
        <- [all {unit place values}]<:{1}>
        <- {carry-over number}*1<:{2}>
        <- {sum}?<:{3}>
    
    <- {remainder} | 1.1.4. imperative
        <= ::(get remainder of {1} divided by 10)
        <- {digit sum}<:{1}>
    
    <- {number pair}<$={1}> | Input collection
```

### Working Interpretation

```python
{
    "syntax": {
        "marker": "every",
        "loop_index": 1,
        "LoopBaseConcept": "{number pair}",
        "CurrentLoopBaseConcept": "{number pair}*1",
        "group_base": "{number pair}",
        "ConceptToInfer": ["{new number pair}"],
        "InLoopConcept": {
            "{carry-over number}*1": 1  # Carry from previous iteration
        }
    },
    "workspace": {},
    "flow_info": {"flow_index": "1"}
}
```

### Execution Flow

**Iteration 1:**
1. GR retrieves first `{number pair}` → `["123", "456"]`
2. LR checks workspace → element is new
3. Inner inferences execute → produce `{digit sum}`, `{remainder}`
4. LR stores result in workspace at index 0
5. LR sets `is_loop_progress = True`
6. OWI checks completion → not done, orchestrator loops back

**Iteration 2:**
1. GR retrieves second `{number pair}`
2. LR retrieves carried `{carry-over number}*1` from workspace[0]
3. Inner inferences execute with carried state
4. LR stores result in workspace at index 1
5. OWI checks completion → not done, loops back

**Iteration 3 (Final):**
1. OWI checks → all elements processed
2. LR aggregates all workspace results into final reference
3. OWI sets `completion_status = True`
4. Orchestrator proceeds to next inference

---

## State Carry-Over

The `InLoopConcept` field defines which concepts should be "carried forward" from previous iterations.

### Carry Index Meaning

```python
"InLoopConcept": {
    "{carry}*1": 1  # Retrieve value from 1 iteration back
    "{sum}*1": 0    # Retrieve initial value (before first iteration)
}
```

- **`0`**: Use the initial value (from `context_concepts`)
- **`1`**: Use the value from the previous iteration
- **`2`**: Use the value from 2 iterations back
- **`N`**: Use the value from N iterations back

### How Carry-Over Works

1. **Initial State**: The `context_concepts` provide the starting values (e.g., `{carry} = 0`)
2. **Iteration 1**: The loop body computes a new `{carry}`
3. **Iteration 2**: The LR step retrieves the `{carry}` from Iteration 1's workspace
4. **Iteration 3**: Retrieves from Iteration 2, and so on...

This enables algorithms like addition (carry digits), accumulators (running totals), and state machines.

---

## Nested Loops

The `loop_index` parameter allows multiple loops to coexist:

```ncd
{result} | Outer loop
    <= *every({collection})@(1)  # loop_index = 1
    
    <- {inner result} | Inner loop
        <= *every({items})@(2)  # loop_index = 2
        
        <- {collection}*1  # Current element from outer loop
```

The workspace keys are namespaced by loop index:
```python
workspace = {
    "1_{collection}": {...},  # Outer loop
    "2_{items}": {...}         # Inner loop
}
```

This prevents workspace collisions between nested loops.

---

## Key Classes and Methods

### `Looper` Class (`infra/_syntax/_looper.py`)

The core logic class that manages workspace operations.

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `retrieve_next_base_element()` | Get the next unprocessed element from the collection |
| `store_new_base_element()` | Store a new element in the workspace |
| `store_new_in_loop_element()` | Store an inferred concept for a specific element |
| `retrieve_next_in_loop_element()` | Get carried state from previous iterations |
| `combine_all_looped_elements_by_concept()` | Aggregate all results into a single reference |
| `check_all_base_elements_looped()` | Determine if the loop is complete |

### `States` Class (`infra/_states/_looping_states.py`)

The state container for the looping sequence.

**Key Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `syntax` | `SimpleNamespace` | Parsed loop configuration |
| `workspace` | `dict` | Persistent workspace across iterations |
| `is_loop_progress` | `bool` | Whether the current iteration added a new element |
| `values` | `list[ReferenceRecordLite]` | Input value concepts |
| `context` | `list[ReferenceRecordLite]` | Loop context (current element, carried state) |
| `inference` | `list[ReferenceRecordLite]` | Step-by-step inference results |

---

## Loop Termination

The loop terminates when **all elements** in the base collection have been processed and stored in the workspace.

**OWI Step Logic:**

1. Retrieve the flattened collection from GR step
2. Iterate through each element
3. Check if that element exists in the workspace
4. Check if the required `ConceptToInfer` exists for that element
5. If all elements are present with their inferred concepts → **complete**
6. Otherwise → **not complete** (orchestrator re-runs loop body)

---

## Comparison to `quantifying`

The **looping** sequence is the successor to **quantifying**. The only differences are naming:

| Old (quantifying) | New (looping) |
|-------------------|---------------|
| `_qr.py` | `_lr.py` |
| `quantifying_references()` | `looping_references()` |
| `quantifier_index` | `loop_index` |
| `is_quantifier_progress` | `is_loop_progress` |
| `Quantifier` class | `Looper` class |

All logic is identical. Both sequences remain available for backward compatibility.

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.getLogger("infra._agent._steps.loop").setLevel(logging.DEBUG)
logging.getLogger("infra._syntax._looper").setLevel(logging.DEBUG)
```

### Inspect the Workspace

Add this to your orchestrator:
```python
from infra._loggers.utils import log_workspace_details
log_workspace_details(workspace, logger)
```

### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Loop never terminates | `ConceptToInfer` not being stored | Check that inner inference produces the expected output |
| State not carrying over | Wrong `carry_index` or missing context concept | Verify `InLoopConcept` config and context setup |
| "Not in workspace" error | Trying to store in-loop concept before base | Ensure base element is stored first |
| Elements processed multiple times | Workspace not persisting | Check that workspace is passed in `working_interpretation` |

---

## Usage Example

### From an Orchestrator

```python
from infra._agent._steps.loop import looping_methods
from infra._states._looping_states import States

# Configure the inference
working_interpretation = {
    "syntax": {
        "marker": "every",
        "loop_index": 1,
        "LoopBaseConcept": "{item}",
        "ConceptToInfer": ["{result}"],
        "group_base": "{item}",
    },
    "workspace": {},
    "flow_info": {"flow_index": "1"}
}

# Initialize states
states = States()

# Execute the pipeline
states = looping_methods["input_working_interpretation"](
    inference, states, body, working_interpretation
)
states = looping_methods["input_references"](inference, states)
states = looping_methods["grouping_references"](states)
states = looping_methods["looping_references"](states)
states = looping_methods["output_reference"](states)
states = looping_methods["output_working_interpretation"](states)

# Check completion
is_complete = getattr(states.syntax, "completion_status", False)
```

---

## See Also

- **NormCode Formalism Guide**: `context_store/shared---normcode_formalism_basic.md`
- **Agent Sequences Guide**: `context_store/shared---normcode_agent_sequence_guide.md`
- **Syntactic Operators Reference**: `context_store/shared---normcode_syntatical_concepts_reconstruction.md`
- **Migration Notes**: `MIGRATION_NOTES.md` (in this directory)
- **Base-X Addition Example**: `infra/examples/add_examples/` (demonstrates nested loops with carry-over)

---

## License & Attribution

Part of the **NormCode** framework for context-isolated AI planning.  
Developed by Xin Guan / PsylensAI

