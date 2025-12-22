# Assigning Sequence

The **assigning sequence** is a syntactic agent sequence that manages data flow through variable assignments, selections, and transformations. It is the execution engine behind the `$` family of operators in NormCode.

---

## Purpose

The assigning sequence allows NormCode plans to:
- **Assign** data from one concept to another (`$.`)
- **Accumulate** data across iterations (`$+`)
- **Select** elements from collections (`$-`)
- **Create** references from literal values (`$%`)
- **Alias** concepts to share identity (`$=`)

This is a **syntactic** (not semantic) sequence—it manipulates references and data structure without invoking LLM reasoning.

---

## The Five-Step Pipeline

The assigning sequence follows a standardized pipeline:

```
IWI → IR → AR → OR → OWI
```

| Step | Name | Purpose |
|------|------|---------|
| **IWI** | Input Working Interpretation | Parse syntax config (marker, sources, selectors) |
| **IR** | Input References | Load concept references from the inference |
| **AR** | Assigning References | Core logic: perform the specified assignment operation |
| **OR** | Output Reference | Finalize output reference |
| **OWI** | Output Working Interpretation | Update execution state |

---

## The Five Assignment Operations

### 1. Identity (`$=`) — **Concept-Level Aliasing**

**Purpose**: Declares that two concepts ARE THE SAME. This is not a reference copy—it's a bidirectional alias at the concept level.

**Syntax Pattern**: `$= %>({source})`

**Example**:
```ncd
{input question}
    <= $= %>({user query})
    <* {user query}
```

**Working Interpretation**:
```python
{
    "syntax": {
        "marker": "=",
        "canonical_concept": "{user query}",
        "alias_concept": "{input question}"
    }
}
```

**Behavior**:
- Both concept names resolve to the same underlying concept
- Completing one completes the other
- They share the same reference
- Status updates apply to both

**Implementation Note**: Identity requires orchestrator-level blackboard access. The AR step sets a flag (`identity_pending`) that the orchestrator must handle via `blackboard.register_identity()`.

---

### 2. Abstraction (`$%`) — **Literal to Reference**

**Purpose**: Creates a Reference directly from a literal face value (ground concept initialization).

**Syntax Pattern**: `$% %>({face_value}) %:([{axis1}, {axis2}])`

**Face Value Forms**:
- **Perceptual sign**: `%{file_location}a1b(data/input.txt)` → singleton
- **Nested list**: `[["123", "456"], ["789"]]` → structured reference
- **Plain string**: `"content"` → singleton

**Examples**:

```ncd
# Singleton perceptual sign
{input file}
    <= $% %>(%{file_location}a1b(data/input.txt))
```

```ncd
# Structured list with explicit axes
{number pair}
    <= $% %>(["123", "456"]) %:([{number}])
```

```ncd
# 2D nested structure
{test matrix}
    <= $% %>([[1, 2], [3, 4]]) %:([{row}, {column}])
```

**Working Interpretation**:
```python
{
    "syntax": {
        "marker": "%",
        "face_value": [["123", "456"], ["789"]],
        "axis_names": ["{pair}", "{number}"]
    }
}
```

**Behavior**:
- Parses the face value to determine if singleton or structured
- If structured and `axis_names` provided, uses them
- If structured without `axis_names`, infers axes from data depth
- Returns a Reference with the literal content as tensor data

---

### 3. Specification (`$.`) — **Select First Valid**

**Purpose**: Extracts a child concept as the value, or selects the first valid reference from multiple candidates.

**Syntax Pattern**: `$. %>({child})` or `$. %>[{option1}, {option2}, ...]`

**Example (Single Source)**:
```ncd
{final result}
    <= $.({remainder})
    <- {remainder}
        <= ::(compute remainder of {1})
```

**Example (Multiple Candidates)**:
```ncd
{output}
    <= $. %>[{cached_result}, {computed_result}]
    <- {cached_result}  # May be None
    <- {computed_result}  # Fallback if cache empty
```

**Working Interpretation**:
```python
{
    "syntax": {
        "marker": ".",
        "assign_source": ["{cached_result}", "{computed_result}"],
        "assign_destination": "{output}"
    }
}
```

**Behavior**:
- Iterates through source references in order
- Returns the first non-None, non-empty reference
- If all sources are invalid, returns destination reference as fallback
- If all are None, returns empty reference

---

### 4. Continuation (`$+`) — **Append Along Axis**

**Purpose**: Appends source reference to destination reference along a specified axis (accumulation).

**Syntax Pattern**: `$+ %>({base}) %<({append_item}) %:({axis})`

**Example**:
```ncd
{number pair}
    <= $+ %>({number pair}) %<({number pair to append}) %:({number pair})
    <- {number pair}  # Existing collection
    <- {number pair to append}  # New item to add
```

**Working Interpretation**:
```python
{
    "syntax": {
        "marker": "+",
        "assign_source": "{number pair to append}",
        "assign_destination": "{number pair}",
        "by_axes": ["{number pair}"]
    }
}
```

**Behavior**:
- Uses `Reference.append()` method
- Appends along the specified axis (or first axis if not specified)
- If destination is None/empty, effectively returns a copy of source
- Preserves axis structure during append

**Use Case**: Accumulating results in loops (e.g., building a list of processed items).

---

### 5. Derelation (`$-`) — **Structural Selection**

**Purpose**: Selects elements from a reference by index, key, or unpacking (pure structural operation).

**Syntax Pattern**: `$- %>({source}) %^(<selection_conditions>)`

**Selection Conditions**:
- `<$*N>` → select at index N
- `<$*-1>` → select last item
- `<$({key})%>` → select by dictionary key
- `<$*#>` → unpack/flatten all

**Examples**:

```ncd
# Select first item
{first_element}
    <= $- %>({collection}) %^(<$*0>)
    <- {collection}
```

```ncd
# Select last item
{last_element}
    <= $- %>({collection}) %^(<$*-1>)
    <- {collection}
```

```ncd
# Select by key
{user_name}
    <= $- %>({user_data}) %^(<$({name})%>)
    <- {user_data}
```

```ncd
# Unpack all elements
{flattened_list}
    <= $- %>({nested_list}) %^(<$*#>)
    <- {nested_list}
```

**Working Interpretation**:
```python
{
    "syntax": {
        "marker": "-",
        "assign_source": "{collection}",
        "selector": {
            "index": 0  # or {"key": "name"} or {"unpack": True}
        }
    }
}
```

**Behavior**:
- Applies selector function via `element_action()`
- Supports index selection (positive or negative)
- Supports key extraction from dictionaries
- Supports unpacking (flattening) lists
- Handles `UnpackedList` special case for multi-element results

---

## Comparison Table

| Operator | Level | Purpose | Example Use Case |
|----------|-------|---------|------------------|
| `$=` | **Concept** | Merge two names | Integrate plans with different naming |
| `$%` | Reference | Literal → Data | Initialize ground concepts |
| `$.` | Reference | Pick first valid | Fallback logic, child extraction |
| `$+` | Reference | Accumulate | Build lists in loops |
| `$-` | Reference | Structural pick | Index/key selection, unpacking |

---

## Working Interpretation Structure

The assigning sequence expects a `working_interpretation` with the following structure:

```python
{
    "syntax": {
        "marker": "=",           # Operation: "=", "%", ".", "+", "-"
        
        # Common fields
        "assign_source": "{src}",           # Source concept(s)
        "assign_destination": "{dest}",     # Destination concept
        
        # Operation-specific fields
        "by_axes": ["{axis}"],              # For continuation ($+)
        "face_value": "...",                # For abstraction ($%)
        "axis_names": ["{ax1}", "{ax2}"],   # For abstraction ($%)
        "selector": {"index": 0},           # For derelation ($-)
        "canonical_concept": "{original}",  # For identity ($=)
        "alias_concept": "{new_name}"       # For identity ($=)
    },
    "workspace": {},
    "flow_info": {"flow_index": "1.2.3"}
}
```

---

## Example: Accumulation in a Loop

This example shows `$+` (continuation) used to accumulate results:

```ncd
{all results}
    <= *every({item})@(1)
        <= $+({result}:{all results})%:[{result}]
        <- {result}
            <= ::(process {1})
            <- {item}*1<:{1}>
        <- {all results}
    <- {items}
```

**Explanation**:
1. Loop processes each `{item}`
2. Each iteration produces a `{result}`
3. Continuation operator `$+` appends `{result}` to `{all results}`
4. After loop completes, `{all results}` contains all accumulated values

---

## Implementation Details

### States Class (`_assigning_states.py`)

Stores all necessary syntax information:

```python
self.syntax = SimpleNamespace(
    marker=None,                  # Operation marker
    assign_source=None,           # Source concept(s)
    assign_destination=None,      # Destination concept
    by_axes=[],                   # Axes for continuation
    face_value=None,              # Literal value for abstraction
    axis_names=None,              # Axes for structured abstraction
    selector=None,                # Selector config for derelation
    canonical_concept=None,       # For identity
    alias_concept=None            # For identity
)
```

### Assigner Class (`_assigner.py`)

Core logic implementation:

| Method | Operation | Returns |
|--------|-----------|---------|
| `identity()` | `$=` | `bool` (needs blackboard) |
| `abstraction()` | `$%` | `Reference` |
| `specification()` | `$.` | `Reference` |
| `continuation()` | `$+` | `Reference` |
| `derelation()` | `$-` | `Callable` (selector function) |

---

## Special Cases

### Identity and Orchestrator Integration

Identity (`$=`) requires blackboard access, which is orchestrator-level. The AR step cannot directly register the alias. Instead:

1. AR sets `states.syntax.identity_pending = True`
2. Orchestrator checks this flag after AR execution
3. Orchestrator calls `blackboard.register_identity(alias, canonical)`

**Orchestrator Pattern**:
```python
states = inference.execute()
if hasattr(states.syntax, 'identity_pending') and states.syntax.identity_pending:
    blackboard.register_identity(
        states.syntax.alias_concept,
        states.syntax.canonical_concept
    )
```

### UnpackedList Handling

When derelation returns multiple elements (via `unpack=True`), the `UnpackedList` wrapper signals that the result should be flattened. The AR step detects this and restructures the output reference accordingly.

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.getLogger("infra._agent._steps.assigning").setLevel(logging.DEBUG)
logging.getLogger("infra._syntax._assigner").setLevel(logging.DEBUG)
```

### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| "assign_source must be specified" | Missing source in syntax | Check working_interpretation syntax |
| Identity not working | Orchestrator not handling flag | Verify orchestrator checks `identity_pending` |
| Continuation wrong axis | `by_axes` not specified | Add `by_axes` to syntax |
| Derelation returns wrong element | Wrong selector config | Check `index`, `key`, or `unpack` fields |
| Abstraction wrong shape | `axis_names` mismatch with data | Ensure axis count matches data dimensions |

---

## See Also

- **Syntactic Operators Reference**: `context_store/shared---normcode_syntatical_concepts_reconstruction.md`
- **Reference System**: Documentation on multi-dimensional references
- **Orchestrator Integration**: How assigning fits into execution flow
- **Looping Sequence**: `infra/_agent/_steps/loop/README.md` (uses `$+` for accumulation)

---

## License & Attribution

Part of the **NormCode** framework for context-isolated AI planning.  
Developed by Xin Guan / PsylensAI

