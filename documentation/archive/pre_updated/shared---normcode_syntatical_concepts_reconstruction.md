# NormCode Syntax Activation (Syntactic Operators Only)

This document defines the **unified syntax** for syntactic operators - operators that manipulate data structure and control flow WITHOUT invoking LLM reasoning.

**Note**: `workspace` and `flow_info` are provided by the orchestrator, NOT extracted from `.ncd` syntax. This document focuses **only on the `syntax` dict** extraction.

---

## Part 0: The Intuition — Why These Operators?

### 0.1. The Fundamental Problem: Indefinite References

When we reason in natural language, we constantly use **indefinite references**:

- "For each **student**, calculate their average grade"
- "Get the **parent** of a student"  
- "If **all numbers** are zero, stop"

The phrase "a student" doesn't refer to a specific person—it's a **placeholder** that could be any student in context. This indeterminacy is not a bug; it's how natural reasoning works.

NormCode models this through **tensor-structured references**: each reference is a multi-dimensional container where dimensions (axes) represent the **modes of indeterminacy**. For example, "a student" might have axes `[school, class, nationality, student]`—each dimension capturing a way the reference could vary.

### 0.2. What Syntactic Operators Do

**Syntactic operators are tensor algebra for AI planning.** They reshape, combine, traverse, and gate references—all WITHOUT looking at the actual content. This is what makes them:

- **Free**: No LLM calls, no token cost
- **Deterministic**: Same input → same output, always
- **Auditable**: You can trace exactly what structure changed

```
┌──────────────────────────────────────────────────────────────┐
│  SEMANTIC operations (imperatives, judgements)               │
│  → CREATE new information via LLM reasoning                  │
│  → Expensive, non-deterministic                              │
├──────────────────────────────────────────────────────────────┤
│  SYNTACTIC operations ($, &, @, *)                           │
│  → RESHAPE existing information via tensor algebra           │
│  → Free, deterministic, auditable                            │
└──────────────────────────────────────────────────────────────┘
```

### 0.3. The Four Operator Families

Each family handles a fundamental aspect of data flow:

---

#### **Assigning (`$`) — "What flows forward?"**

Assigning controls **which data** gets stored in a concept. It answers: "Given these options, what should the result be?"

| Marker | Natural Language | Level | Effect |
|--------|------------------|-------|--------|
| `$=` | "This IS that" | **Concept** | Merge two concepts as one (alias) |
| `$%` | "This literal IS the data" | Reference | Reify definition as reference |
| `$.` | "Use THIS one" | Reference | Pick first valid from options |
| `$+` | "Add this to that" | Reference | Extend along an axis |
| `$-` | "Get X from Y" | Reference | Extract/select from structure |

**Important distinction**:
- `$=` is a **concept-level** operation: it tells the orchestrator that two concept names refer to the same thing
- `$%`, `$.`, `$+`, `$-` are **reference-level** operations: they manipulate the data stored in references

**Intuition**: Think of assigning as **routing**. Data arrives at a junction; assigning decides where it goes.

```
$=  →  Merge lanes (two names, one road)  ← concept-level
$%  →  On-ramp (literal becomes data)     ← reference-level  
$.  →  Switch (pick first valid)          ← reference-level
$+  →  Extend lane (accumulate)           ← reference-level
$-  →  Filter/extract (structural pick)   ← reference-level
```

**Use case for `$=`**: When integrating two NormCode plans that define the same concept with different names:
```
Plan A: {user query}
Plan B: {input question}

Integration: {input question} $= {user query}
→ Both names now resolve to the SAME concept
→ Completing one completes the other
```

---

#### **Grouping (`&`) — "How do references combine?"**

Grouping controls how **multiple references** merge into one. It manages axes—which to collapse, which to preserve.

| Marker | Natural Language | Tensor Effect |
|--------|------------------|---------------|
| `&[{}]` | "Bundle these with labels" | Collapse axis → dict elements |
| `&[#]` | "Collect these into a list" | Collapse axis → flat list |

**Intuition**: Think of grouping as **packaging**. You have several items; grouping decides the container structure.

```
&[{}]  →  Labeled boxes (each item keeps its name)
           {"query": ..., "context": ...}
           
&[#]   →  Single pile (items lose source identity)
           [item1, item2, item3, ...]
```

**Why two modes?** Sometimes you need to access items by name later (`&[{}]`). Sometimes you just need all items together (`&[#]`).

---

#### **Timing (`@`) — "When does this happen?"**

Timing controls **execution flow**—whether an operation runs, and in what order.

| Marker | Natural Language | Effect |
|--------|------------------|--------|
| `@:'` | "If X is true, do this" | Gate on condition |
| `@:!` | "If X is NOT true, do this" | Gate on negation |
| `@.` | "After X completes, do this" | Sequence dependency |

**Intuition**: Think of timing as **traffic control**. Operations wait at gates until conditions are met.

```
@:'  →  Green light (proceed if true)
@:!  →  Red light bypass (proceed if false)
@.   →  Yield sign (wait for dependency)
```

---

#### **Looping (`*`) — "How do we traverse?"**

Looping controls **iteration** over collections—processing each element while carrying state forward.

| Marker | Natural Language | Effect |
|--------|------------------|--------|
| `*.` | "For each X, do Y" | Traverse axis, carry state |

**Intuition**: Think of looping as **walking through a list**. At each step, you:
1. Take the current element
2. Do something with it
3. Carry results to the next step

```
*.  →  For each item in collection:
         - Get current item
         - Process it  
         - Accumulate result
         - Carry state to next iteration
```

**Why carry state?** Many algorithms need to remember something between iterations (like a running total or carry-over digit).

---

### 0.4. How They Work Together

A typical inference chain:

```
1. LOOP (*)      : "For each document..."
2. GROUP (&)     : "...combine its title and body..."
3. [SEMANTIC]    : "...summarize them..." (LLM call)
4. ASSIGN ($)    : "...and add the summary to results"
5. TIME (@)      : "After all summaries, proceed to..."
```

The syntactic operators handle steps 1, 2, 4, 5—all the **structural plumbing**—so the semantic operation (step 3) receives exactly what it needs.

### 0.5. The Key Insight

**Syntactic operators are context-agnostic.** 

When `$+` appends a summary to a collection, it doesn't know what a "summary" means. It only knows:
- Source reference has shape `[document]`
- Destination has shape `[document, summary]`
- Append along the `summary` axis

This separation is what makes NormCode plans **auditable**: every structural transformation is explicit and traceable, independent of content.

---

## Part 1: Unified Modifier System

All syntactic operators share a common vocabulary of **modifiers**. This provides consistency across operator types and simplifies parsing.

### 1.1. Modifier Reference

| Modifier | Name | Meaning | Direction |
|----------|------|---------|-----------|
| `%>` | Source | Input / Read from | `>` points AT the source |
| `%<` | Target | Output / Write to | `<` points TO the target |
| `%:` | Axis | Context axis / Base | Structural dimension |
| `%^` | Carry | Carried state / Selection | Contextual state |
| `%@` | Index | Quantifier ID / Number | Iteration identifier |

### 1.2. Inline Annotations

| Annotation | Meaning | Example |
|------------|---------|---------|
| `<$!{...}>` | Protection | `<$!{%(class)}>` = don't transform this axis |
| `<$*N>` | Iteration version | `*1` = loop 1 current, `*-1` = previous iteration |
| `<$*0>` | Initial value | The starting state before any iteration |
| `<$({key})%>` | Key selection | Select by dictionary key |
| `<$*#>` | Unpack all | Spread/flatten the collection |

### 1.3. Iteration Version Semantics (`*N`)

| Notation | Meaning |
|----------|---------|
| `*0` | Initial value (before first iteration) |
| `*1`, `*2`, ... | Current value in loop 1, loop 2 (for nested loops) |
| `*-1` | Previous iteration's value (relative to current) |
| `*-N` | N iterations back |
| `*N` (where N > current) | Capped to current iteration |

### 1.4. Bracket Convention

- **Single item**: Use parentheses `()`
- **Multiple items**: Use brackets `[]`

Example:
- `%>({single_source})`
- `%>[{source_1}, {source_2}]`

---

## Part 2: Operator Specifications

### 2.1. Sequence Identifiers

| Symbol | Sequence | Description |
|--------|----------|-------------|
| `$` | Assigning | Data assignment and selection |
| `&` | Grouping | Collection creation and flattening |
| `@` | Timing | Conditional and sequential execution |
| `*` | Looping | Iteration over collections |

### 2.2. Operator Markers

| Sequence | Marker | Symbol | Meaning |
|----------|--------|--------|---------|
| **Assigning** | `=` | `$=` | Identity (copy/alias) |
| | `.` | `$.` | Specification (extract child) |
| | `+` | `$+` | Continuation (append) |
| | `-` | `$-` | Selection (filter/index) |
| | `%` | `$%` | Abstraction (template) |
| **Grouping** | `[{}]` | `&[{}]` | Group In (collect into container) |
| | `[#]` | `&[#]` | Group Across (flatten over axis) |
| **Timing** | `:'` | `@:'` | Conditional (if true) |
| | `:!` | `@:!` | Negated conditional (if false) |
| | `.` | `@.` | Sequencing (after dependency) |
| **Looping** | `.` | `*.` | Iterate (for every item) |

---

## Part 3: Syntax Patterns

### 3.1. General Pattern

```
<sequence><marker> [%>(<sources>)] [%<(<targets>)] [%:(<axes>)] [%^(<carried>)] [%@(<index>)]
```

All modifiers are optional; only include what's needed for the operation.

### 3.2. Assigning Operators

#### Identity (`$=`) — Concept-Level Merge
Declares that two concepts ARE THE SAME. This is **not** a reference copy—it's a concept-level alias that merges two names into one.

**Pattern**: `$= %>({source})`

**Example**:
```ncd
{input question}
    <= $= %>({user query})
    <* {user query} 
```
**Old syntax**: `$=({user query})`

**Semantics**:
- After execution, `{input question}` and `{user query}` resolve to the **same concept**
- They share the same reference and status
- Completing one completes the other
- This is bidirectional: looking up either name finds the same underlying data

**Use case**: Integrating two NormCode plans that define the same logical concept with different names.

**Extraction**:
```python
{
    "marker": "=",
    "mode": "identity",
    "alias_concept": "{input question}",      # The new name (from concept_to_infer)
    "canonical_concept": "{user query}"       # The existing name (from source)
}
```

**Orchestrator behavior**:
1. Calls `blackboard.register_identity(alias_concept, canonical_concept)`
2. Both names now resolve to the same canonical concept
3. Status, reference, and completion are shared

---

#### Abstraction (`$%`) — Reify Definition as Data
Takes a **face value** (literal definition) and creates a Reference from it directly. This reifies the definition itself as data rather than looking up a computed reference.

**Pattern**: `$% %>({face_value}) %:([{axis1}, {axis2}])`

**Face Value Forms**:

| Form | Meaning | Result |
|------|---------|--------|
| `%{norm}...(content)` | Perceptual sign | Singleton reference |
| `[[val1, val2], ...]` | Nested list | Structured reference with axes |
| `"plain string"` | Plain value | Singleton reference |

**Examples**:

```ncd
# Singleton perceptual sign (ground concept with file reference)
{input file}
    <= $% %>(%{file_location}a1b(data/input.txt))
```

```ncd
# Structured list with explicit axes
{number pair}
    <= $% %>(["123", "456"]) %:([{number}])
```

```ncd
# Nested structure (2D)
{test matrix}
    <= $% %>([[1, 2], [3, 4]]) %:([{row}, {column}])
```

**Extraction**:
```python
{
    "marker": "%",
    "mode": "abstraction",
    "face_value": "%{file_location}a1b(data/input.txt)",  # or [[...]]
    "axis_names": ["{number}"]  # Optional, from %:
}
```

**Use cases**:
- Ground concept initialization (defining literal data)
- Template definitions (perceptual signs as data)
- Test fixtures and examples

**Behavior**:
1. Parse `face_value` to determine if singleton or structured
2. If structured and `axis_names` provided, use them
3. Create Reference with the literal content as tensor data

---

#### Specification (`$.`)
Extracts a child concept as the value.

**Pattern**: `$. %>({child})`

**Example**:
```ncd
$. %>({remainder})
```
**Old syntax**: `$.({remainder})`

**Extraction**:
```python
{
    "marker": ".",
    "assign_source": "{remainder}",
    "assign_destination": <from concept_to_infer>
}
```

---

#### Continuation (`$+`)
Appends source to target along an axis.

**Pattern**: `$+ %>({base}) %<({append_item}) %:({axis})`

**Example**:
```ncd
$+ %>({number pair}) %<({number pair to append}) %:({number pair})
```
**Old syntax**: `$+({number pair to append}:{number pair})%:[{number pair}]`

**Extraction**:
```python
{
    "marker": "+",
    "assign_source": "{number pair to append}",
    "assign_destination": "{number pair}",
    "by_axes": ["{number pair}"]
}
```

---

#### Selection (`$-`)
Selects elements from source by index, key, or unpacking.

**Pattern**: `$- %>({source}) %^(<selection_conditions>)`

**Selection Conditions**:
- `<$*N>` = select at index N
- `<$({key})%>` = select by key
- `<$*#>` = unpack all

**Example**:
```ncd
$- %>({collection}) %^(<$*0>)           # Select first item
$- %>({collection}) %^(<$*-1>)          # Select last item
$- %>({dict}) %^(<$({my_key})%>)        # Select by key
$- %>({list}) %^(<$*#>)                 # Unpack all
```

**Extraction**:
```python
{
    "marker": "-",
    "assign_source": "{collection}",
    "selection": {"index": 0}  # or {"key": "my_key"} or {"unpack": True}
}
```

---

### 3.3. Grouping Operators

#### Understanding Grouping Intuitively

Grouping is about **combining references** and **managing their axes**. Think of it like this:

| Component | Intuition |
|-----------|-----------|
| **Sources (`%>`)** | The references to combine |
| **by_axis (`%:`)** | Axes to "collapse" (remove from output) |
| **protect_axes (`<$!...>`)** | Axes to KEEP even if they'd normally be collapsed |

**What happens during grouping** (from `_grouper.py`):
1. Find shared axes across all source references
2. Align sources on shared axes (cross product)
3. Remove `by_axes` from the result (collapse those dimensions)
4. BUT keep any `protect_axes` (don't collapse those)

---

#### Group In (`&[{}]`) — "Collect into a labeled container"

**Intuition**: Like putting items in a labeled box. Each item keeps its name/identity.

```
Input: {A} = [1, 2, 3], {B} = ["x", "y", "z"]
Output: [{"A": 1}, {"A": 2}, {"A": 3}, {"B": "x"}, {"B": "y"}, {"B": "z"}]  (annotated elements)
```

**Implementation** (`Grouper.and_in()`):
- **Legacy mode**: Cross product + annotate
- **Per-reference mode**: Collapse each input's specified axes, annotate, concatenate, wrap in new axis

**Pattern**: 
- Legacy: `&[{}] %>[{item_1}, {item_2}, ...] %:({collapse_axis}<$!{keep_axis}>)`
- Per-reference: `&[{}] %>[{item_1}, {item_2}, ...] %+({axis_name})`

**Example (Legacy)**:
```ncd
&[{}] %>[{original prompt}, {other input files}] %:({input type}<$!{%(class)}>)
```
- Collects `{original prompt}` and `{other input files}` into a dict
- Collapses the `{input type}` axis (if it exists)
- BUT protects `{%(class)}` axis (keeps it even if shared)

**Example (Per-Reference with create_axis)**:
```ncd
[all recommendations]
    <= &[{}] %>[{bullish recommendation}, {bearish recommendation}, {neutral recommendation}] %+(recommendation)
```

Where `%+(recommendation)` explicitly names the new axis dimension.

**Extracted configuration**:
```python
{
    "by_axes": [["bullish_recommendation"], ["bearish_recommendation"], ["neutral_recommendation"]],
    "create_axis": "recommendation"  # From %+(recommendation)
}
```
- Collapses each input along its specified axis
- Annotates each element: `{"{bullish recommendation}": value}`, etc.
- Creates new Reference with axes: `[recommendation]`

**Old syntax**: `&in` with value concepts listed separately

**Extraction**:
```python
# Legacy format
{
    "marker": "in",
    "by_axis_concepts": [],      # For &in, sources are in value_concepts
    "protect_axes": ["{%(class)}"]
}

# New per-reference format
{
    "marker": "in",
    "by_axes": [["ax1"], ["ax2"], ...],  # Per-reference axes to collapse
    "create_axis": "recommendation",      # Name for resulting axis
    "protect_axes": []
}
```

---

#### Group Across (`&[#]`) — "Flatten into a unified list or axis"

**Intuition**: Like pouring items from multiple containers into one pile. Items lose their source identity but stay as a flat list.

```
Input: {A} = [1, 2], {B} = [3, 4]
Output: [1, 2, 3, 4]  (flat list)
```

**Implementation** (`Grouper.or_across()`):
- **Legacy mode**: Cross product + flatten
- **Per-reference mode**: Collapse each input's specified axes, concatenate, wrap in new axis

**Pattern**: 
- Legacy: `&[#] %>({source}) %:({collapse_axis})`
- Per-reference: `&[#] %>[{s1}, {s2}, ...] %+({axis_name})`

**Example (Legacy)**:
```ncd
&[#] %>({number pair}*1) %:({number})
```
- Takes `{number pair}*1` (a pair of numbers in the current loop iteration)
- Collapses the `{number}` axis (removes the "which number in the pair" dimension)
- Flattens into a single list of digit values

**Example (Per-Reference with create_axis)**:
```ncd
{validated signal}
    <= &[#] %>[{quantitative signal}, {narrative signal}, {theoretical framework}] %+(signal)
```

Where `%+(signal)` explicitly names the new axis dimension.

**Extracted configuration**:
```python
{
    "by_axes": [["quantitative_signal"], ["narrative_signal"], ["_none_axis"]],
    "create_axis": "signal"  # From %+(signal)
}
```
- Collapses each input along its specified axis
- Concatenates all resulting elements (e.g., 2 + 1 + 1 = 4 items)
- Creates new Reference with axes: `[signal]`, shape: `(4,)`

**Old syntax**: `&across({unit place value}:{number pair}*1)`

**Extraction**:
```python
# Legacy format
{
    "marker": "across",
    "by_axis_concepts": ["{number pair}*1"],  # Source to iterate across
    "protect_axes": []
}

# New per-reference format
{
    "marker": "across",
    "by_axes": [["ax1"], ["ax2"], ...],  # Per-reference axes to collapse
    "create_axis": "signal",              # Name for resulting axis
    "protect_axes": []
}
```

---

#### Visual Comparison

```
&[{}] (Group In):
  ┌─────────────────────┐
  │ {A}: [val1, val2]   │  ← Labeled structure
  │ {B}: [val3, val4]   │
  └─────────────────────┘

&[#] (Group Across):
  ┌─────────────────────┐
  │ [val1, val2, val3, val4] │  ← Flat list
  └─────────────────────┘
```

---

#### When to Use Which?

| Use Case | Operator | Why |
|----------|----------|-----|
| Collect named inputs for a function | `&[{}]` | Need to access by name later |
| Flatten a collection for iteration | `&[#]` | Just need all items, not their source |
| Build a dict-like structure | `&[{}]` | Keys are concept names |
| Concatenate lists | `&[#]` | Merge into one sequence |

---

### 3.4. Timing Operators

#### Conditional (`@:'`)
Executes if condition is true.

**Pattern**: `@:' (<condition>)`

**Example**:
```ncd
@:' (<carry-over number is 0>)
```
**Old syntax**: `@if(<carry-over number is 0>)`

**Extraction**:
```python
{
    "marker": "if",
    "condition": "<carry-over number is 0>"
}
```

---

#### Negated Conditional (`@:!`)
Executes if condition is false.

**Pattern**: `@:! (<condition>)`

**Example**:
```ncd
@:! (<all number is 0>)
```
**Old syntax**: `@if!(<all number is 0>)`

**Extraction**:
```python
{
    "marker": "if!",
    "condition": "<all number is 0>"
}
```

---

#### Sequencing (`@.`)
Executes after dependency completes.

**Pattern**: `@. ({dependency})`

**Example**:
```ncd
@. ({digit sum})
```
**Old syntax**: `@after({digit sum})`

**Extraction**:
```python
{
    "marker": "after",
    "condition": "{digit sum}"
}
```

---

### 3.5. Looping Operator

#### Iterate (`*.`)
Iterates over every item in a collection.

**Pattern**: 
```
*. %>({base}<$({current})*>) %<({result}) %:({axis}) %^({carried}<$({carried})*-1>) %@({index})
```

**Components**:
- `%>({base}<$({current})*>)` - Source collection, with current iteration marker
- `%<({result})` - Concept to infer (output of each iteration)
- `%:({axis})` - Axis to iterate over
- `%^({carried}<$({carried})*-1>)` - Carried state from previous iteration
- `%@({index})` - Quantifier index (1 for outermost loop, 2 for nested, etc.)

**Example**:
```ncd
*. %>({number pair}<$({number pair})*1>) %<({new number pair}) %:({number pair}) %^({carry-over number}<$({carry-over number})*-1>) %@(1)
```
**Old syntax**: `*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]`

**Extraction**:
```python
{
    "marker": "every",
    "quantifier_index": 1,
    "LoopBaseConcept": "{number pair}",
    "CurrentLoopBaseConcept": "{number pair}*1",
    "group_base": "{number pair}",
    "InLoopConcept": {"{carry-over number}*1": 1},
    "ConceptToInfer": ["{new number pair}"]
}
```

---

## Part 4: Mapping Old Syntax to New

| Operator | Old Syntax | New Syntax |
|----------|-----------|------------|
| Identity | `$=({source})` | `$= %>({source})` |
| Abstraction | *(ground concept data)* | `$% %>({literal}) %:([{axes}])` |
| Specification | `$.({child})` | `$. %>({child})` |
| Continuation | `$+({src}:{dest})%:[{axis}]` | `$+ %>({dest}) %<({src}) %:({axis})` |
| Selection | *(not implemented)* | `$- %>({src}) %^(<selector>)` |
| Group In | `&in` + value concepts | `&[{}] %>[{items}] %:({axis})` |
| Group Across | `&across({item}:{src})` | `&[#] %>({src}) %:({item})` |
| If | `@if(<cond>)` | `@:' (<cond>)` |
| If Not | `@if!(<cond>)` | `@:! (<cond>)` |
| After | `@after({dep})` | `@. ({dep})` |
| Every | `*every(...)%:[...]@(N)^[...]` | `*. %>(...) %<(...) %:(...) %^(...) %@(N)` |

---

## Part 5: Design Rationale

### 5.1. Why This Unified System?

1. **Consistency**: All operators use the same modifier vocabulary (`%>`, `%<`, `%:`, `%^`, `%@`)
2. **Language-agnostic**: No English words in the formal `.ncd` representation
3. **Explicit roles**: Every piece of data has a labeled role (source, target, axis, etc.)
4. **Extensible**: New modifiers can be added without breaking existing syntax
5. **Parseable**: All use `%X(...)` pattern for uniform regex extraction

### 5.2. Modifier Mnemonics

- `%>` = **source** ("arrow pointing AT what we read")
- `%<` = **target** ("arrow pointing TO where we write")
- `%:` = **axis** (colon suggests "along this dimension")
- `%^` = **carry** (caret = "lift and carry forward")
- `%@` = **index** (at-sign = "at position N")
- `%+` = **create** (plus sign = "add a new dimension")

### 5.3. Iteration Semantics

The `*N` system is unified:
- Positive N (`*1`, `*2`) = current value in nested loop N
- Zero (`*0`) = initial value before any iteration
- Negative N (`*-1`, `*-2`) = relative to current (previous iterations)

This allows loops to reference both their own state and parent loop states cleanly.

---

## Part 6: Next Steps

1. ✅ Define unified modifier system
2. ✅ Document all operator patterns
3. ✅ Create old → new mapping
4. ⏳ Update IWI implementations to accept new syntax
5. ⏳ Implement parser for new syntax
6. ⏳ Test with real examples (base-X addition, phase_1)
