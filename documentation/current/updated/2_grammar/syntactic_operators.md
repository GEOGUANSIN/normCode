# Syntactic Operators

**The operators that control data flow without calling LLMs—free, deterministic, and auditable.**

---

## Overview

Syntactic operators are **tensor algebra for AI planning**. They reshape, combine, traverse, and gate references—all WITHOUT looking at actual content.

This makes them:
- **Free**: No LLM calls, no token cost
- **Deterministic**: Same input → same output, always
- **Auditable**: Trace exactly what structure changed

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

---

## The Fundamental Problem: Indefinite References

When we reason in natural language, we use **indefinite references**:

- "For each **student**, calculate their average grade"
- "Get the **parent** of a student"
- "If **all numbers** are zero, stop"

The phrase "a student" doesn't refer to a specific person—it's a **placeholder** that could be any student in context.

NormCode models this through **tensor-structured references**: each reference is a multi-dimensional container where dimensions (axes) represent **modes of indeterminacy**.

**Syntactic operators manipulate these tensor structures** to control how data flows through the plan.

---

## The Four Operator Families

Each family handles a fundamental aspect of data flow:

| Symbol | Family | Purpose | Natural Language |
|--------|--------|---------|------------------|
| `$` | **Assigning** | What flows forward? | "Use this", "Add to that" |
| `&` | **Grouping** | How do references combine? | "Collect these", "Bundle together" |
| `@` | **Timing** | When does this happen? | "If X then Y", "After A do B" |
| `*` | **Looping** | How do we traverse? | "For each X do Y" |

---

## Assigning (`$`) — "What flows forward?"

Assigning controls **which data** gets stored in a concept. It answers: "Given these options, what should the result be?"

### The Five Assigning Operators

| Marker | Symbol | Meaning | Level |
|--------|--------|---------|-------|
| **Identity** | `$=` | "This IS that" (alias) | Concept |
| **Abstraction** | `$%` | "This literal IS the data" | Reference |
| **Specification** | `$.` | "Use THIS one" (pick first valid) | Reference |
| **Continuation** | `$+` | "Add this to that" (append) | Reference |
| **Selection** | `$-` | "Get X from Y" (extract) | Reference |

**Important distinction**:
- `$=` is **concept-level**: merges two concept names
- `$%`, `$.`, `$+`, `$-` are **reference-level**: manipulate data

### Intuition: Routing

Think of assigning as **routing**. Data arrives at a junction; assigning decides where it goes:

```
$=  →  Merge lanes (two names, one road)  ← concept-level
$%  →  On-ramp (literal becomes data)     ← reference-level
$.  →  Switch (pick first valid)          ← reference-level
$+  →  Extend lane (accumulate)           ← reference-level
$-  →  Filter/extract (structural pick)   ← reference-level
```

---

### Identity (`$=`) — Concept-Level Merge

Declares that two concepts ARE THE SAME. This is **not** a reference copy—it's a concept-level alias.

**Pattern**: `$= %>({source})`

**Example**:
```ncd
{input question}
    <= $= %>({user query})
    <* {user query}
```

**Semantics**:
- After execution, `{input question}` and `{user query}` resolve to the **same concept**
- They share the same reference and status
- Completing one completes the other
- Bidirectional: looking up either name finds the same data

**Use case**: Integrating two NormCode plans that define the same logical concept with different names.

---

### Abstraction (`$%`) — Reify Definition as Data

Takes a **face value** (literal definition) and creates a Reference from it directly.

**Pattern**: `$% %>({face_value}) %:([{axis1}, {axis2}])`

**Face Value Forms**:

| Form | Meaning | Result |
|------|---------|--------|
| `%{norm}...(content)` | Perceptual sign | Singleton reference |
| `[[val1, val2], ...]` | Nested list | Structured reference with axes |
| `"plain string"` | Plain value | Singleton reference |

**Examples**:

```ncd
# Singleton perceptual sign (file reference)
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

**Use cases**:
- Ground concept initialization (defining literal data)
- Template definitions (perceptual signs as data)
- Test fixtures and examples

---

### Specification (`$.`) — Extract Child Concept

Extracts a child concept as the value (selects the first valid from options).

**Pattern**: `$. %>({child})`

**Example**:
```ncd
{remainder}
    <= $. %>({remainder})
    <- {remainder}
        <= ::(calculate remainder)
        <- {digit sum}
```

**Use case**: Selecting the first non-empty result from multiple options.

---

### Continuation (`$+`) — Append Along Axis

Appends source to target along a specified axis.

**Pattern**: `$+ %>({base}) %<({append_item}) %:({axis})`

**Example**:
```ncd
{updated list}
    <= $+ %>({current list}) %<({new item}) %:({items})
    <- {current list}
    <- {new item}
```

**Use case**: Accumulating results in a loop (growing a collection).

---

### Selection (`$-`) — Extract by Index/Key/Unpack

Selects elements from source by index, key, or unpacking.

**Pattern**: `$- %>({source}) %^(<selection_conditions>)`

**Selection Conditions**:
- `<$*N>` = select at index N
- `<$({key})%>` = select by key
- `<$*#>` = unpack all

**Examples**:
```ncd
$- %>({collection}) %^(<$*0>) /: Select first item
$- %>({collection}) %^(<$*-1>) /: Select last item
$- %>({dict}) %^(<$({my_key})%>) /: Select by key
$- %>({list}) %^(<$*#>) /: Unpack all
```

**Use case**: Extracting specific elements from structured data.

---

## Grouping (`&`) — "How do references combine?"

Grouping controls how **multiple references** merge into one. It manages axes—which to collapse, which to preserve.

### The Two Grouping Operators

| Marker | Symbol | Meaning | Result |
|--------|--------|---------|--------|
| **Group In** | `&[{}]` | "Bundle with labels" | Dict-like structure |
| **Group Across** | `&[#]` | "Collect into list" | Flat list |

### Intuition: Packaging

Think of grouping as **packaging**. You have several items; grouping decides the container structure:

```
&[{}]  →  Labeled boxes (each item keeps its name)
          {"query": ..., "context": ...}
          
&[#]   →  Single pile (items lose source identity)
          [item1, item2, item3, ...]
```

**Why two modes?** Sometimes you need to access items by name later (`&[{}]`). Sometimes you just need all items together (`&[#]`).

---

### Group In (`&[{}]`) — Collect into Labeled Container

**Intuition**: Like putting items in a labeled box. Each item keeps its name/identity.

**Patterns**:
- **Legacy**: `&[{}] %>[{item_1}, {item_2}, ...] %:({collapse_axis}<$!{keep_axis}>)`
- **Current (recommended)**: `&[{}] %>[{item_1}, {item_2}, ...] %+({new_axis_name})`

> **Note**: The `%+({axis_name})` syntax is preferred as it explicitly names the resulting axis, making plans more readable and maintainable.

**Example (Legacy)**:
```ncd
{all inputs}
    <= &[{}] %>[{original prompt}, {other input files}] %:({input type}<$!{%(class)}>)
    <- {original prompt}
    <- {other input files}
    <* {input type}
    <* {%(class)}
```

**Effect**:
- Collects items into a dict-like structure
- Collapses the `{input type}` axis
- BUT protects `{%(class)}` axis (keeps it even if shared)

**Example (Current/Recommended - Per-Reference with create_axis)**:
```ncd
[all recommendations]
    <= &[{}] %>[{bullish recommendation}, {bearish recommendation}, {neutral recommendation}] %+(recommendation)
    <- {bullish recommendation}
    <- {bearish recommendation}
    <- {neutral recommendation}
```

**Explanation**: The `%+(recommendation)` modifier explicitly names the new axis dimension. This is clearer than implicit axis generation and allows each input to be collapsed independently before grouping.

**Result**:
```python
{
    "recommendation": [
        {"{bullish recommendation}": value1},
        {"{bearish recommendation}": value2},
        {"{neutral recommendation}": value3}
    ]
}
```

---

### Group Across (`&[#]`) — Flatten into Unified List

**Intuition**: Like pouring items from multiple containers into one pile. Items lose their source identity.

**Patterns**:
- **Legacy**: `&[#] %>({source}) %:({collapse_axis})`
- **Current (recommended)**: `&[#] %>[{s1}, {s2}, ...] %+({new_axis_name})`

> **Note**: The `%+({axis_name})` syntax is preferred as it explicitly names the resulting axis and works better with per-reference collapsing.

**Example (Legacy)**:
```ncd
{all digits}
    <= &[#] %>({number pair}*1) %:({number})
    <- {number pair}*1
```

**Effect**:
- Takes `{number pair}*1` (a pair of numbers)
- Collapses the `{number}` axis
- Flattens into a single list of digit values

**Example (Current/Recommended - Per-Reference with create_axis)**:
```ncd
{validated signal}
    <= &[#] %>[{quantitative signal}, {narrative signal}, {theoretical framework}] %+(signal)
    <- {quantitative signal}
    <- {narrative signal}
    <- {theoretical framework}
```

**Explanation**: The `%+(signal)` modifier explicitly names the new axis dimension. Each input is collapsed along its own axis, then all are concatenated and wrapped in the new `[signal]` axis.

**Result**: A flat list with axes `[signal]` containing all elements.

---

### Visual Comparison

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

### When to Use Which?

| Use Case | Operator | Why |
|----------|----------|-----|
| Collect named inputs for a function | `&[{}]` | Need to access by name later |
| Flatten a collection for iteration | `&[#]` | Just need all items, not their source |
| Build a dict-like structure | `&[{}]` | Keys are concept names |
| Concatenate lists | `&[#]` | Merge into one sequence |

---

## Timing (`@`) — "When does this happen?"

Timing controls **execution flow**—whether an operation runs, and in what order.

### The Three Timing Operators

| Marker | Symbol | Meaning | Effect |
|--------|--------|---------|--------|
| **Conditional** | `@:'` | "If X is true, do this" | Gate on condition |
| **Negated** | `@:!` | "If X is NOT true, do this" | Gate on negation |
| **Sequencing** | `@.` | "After X completes, do this" | Sequence dependency |

### Intuition: Traffic Control

Think of timing as **traffic control**. Operations wait at gates until conditions are met:

```
@:'  →  Green light (proceed if true)
@:!  →  Red light bypass (proceed if false)
@.   →  Yield sign (wait for dependency)
```

---

### Conditional (`@:'`) — Execute If True

**Pattern**: `@:' (<condition>)`

**Example**:
```ncd
{final output}
    <= @:'(<validation passed>)
    <- {validated output}
    <- <validation passed>
```

**Behavior**: Only executes if `<validation passed>` evaluates to `True`.

---

### Negated Conditional (`@:!`) — Execute If False

**Pattern**: `@:! (<condition>)`

**Example**:
```ncd
{loop continues}
    <= @:!(<all numbers processed>)
    <- {next iteration}
    <- <all numbers processed>
```

**Behavior**: Only executes if `<all numbers processed>` evaluates to `False`.

---

### Sequencing (`@.`) — Execute After Dependency

**Pattern**: `@. ({dependency})`

**Example**:
```ncd
{remainder}
    <= @.({digit sum})
    <- {remainder}
        <= ::(calculate remainder of digit sum)
        <- {digit sum}
```

**Behavior**: Only executes after `{digit sum}` has been computed.

---

## Looping (`*`) — "How do we traverse?"

Looping controls **iteration** over collections—processing each element while carrying state forward.

### The Looping Operator

| Marker | Symbol | Meaning | Effect |
|--------|--------|---------|--------|
| **Iterate** | `*.` | "For each X, do Y" | Traverse axis, carry state |

### Intuition: Walking Through a List

Think of looping as **walking through a list**. At each step, you:
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

### Iterate (`*.`) — For Every Item

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
{all summaries}
    <= *. %>({documents}<$({document})*1>) %<({summary}) %:({document}) %^() %@(1)
    <- {summary}
        <= ::(summarize this document)
        <- {document}*1
    <* {documents}
    <* {document}*1<*{documents}>
```

**Iteration version markers**:
- `*1`, `*2`, ... = Current value in loop 1, loop 2 (for nested loops)
- `*0` = Initial value (before first iteration)
- `*-1` = Previous iteration's value
- `*-N` = N iterations back

---

## The Unified Modifier System

All syntactic operators share a common vocabulary of **modifiers**. This provides consistency across operator types.

### Modifier Reference

| Modifier | Name | Meaning | Direction |
|----------|------|---------|-----------|
| `%>` | Source | Input / Read from | `>` points AT the source |
| `%<` | Target | Output / Write to | `<` points TO the target |
| `%:` | Axis | Context axis / Base | Structural dimension |
| `%^` | Carry | Carried state / Selection | Contextual state |
| `%@` | Index | Quantifier ID / Number | Iteration identifier |
| `%+` | Create | Create new axis | New dimension name |

### Inline Annotations

| Annotation | Meaning | Example |
|------------|---------|---------|
| `<$!{...}>` | Protection | `<$!{%(class)}>` = don't collapse this axis |
| `<$*N>` | Iteration version | `*1` = loop 1 current, `*-1` = previous |
| `<$*0>` | Initial value | The starting state before any iteration |
| `<$({key})%>` | Key selection | Select by dictionary key |
| `<$*#>` | Unpack all | Spread/flatten the collection |

### Bracket Convention

- **Single item**: Use parentheses `()`
- **Multiple items**: Use brackets `[]`

Example:
- `%>({single_source})`
- `%>[{source_1}, {source_2}]`

---

## How They Work Together

A typical inference chain:

```
1. LOOP (*)      : "For each document..."
2. GROUP (&)     : "...combine its title and body..."
3. [SEMANTIC]    : "...summarize them..." (LLM call)
4. ASSIGN ($)    : "...and add the summary to results"
5. TIME (@)      : "After all summaries, proceed to..."
```

The syntactic operators handle steps 1, 2, 4, 5—all the **structural plumbing**—so the semantic operation (step 3) receives exactly what it needs.

---

## The Key Insight: Context-Agnostic Operations

**Syntactic operators don't look at content.**

When `$+` appends a summary to a collection, it doesn't know what a "summary" means. It only knows:
- Source reference has shape `[document]`
- Destination has shape `[document, summary]`
- Append along the `summary` axis

This separation is what makes NormCode plans **auditable**: every structural transformation is explicit and traceable, independent of content.

---

## Mapping Old Syntax to New

| Operator | Old Syntax | Unified Syntax (2023) | Current (2024+) |
|----------|-----------|----------------------|-----------------|
| Identity | `$=({source})` | `$= %>({source})` | ← Same |
| Abstraction | *(ground concept data)* | `$% %>({literal}) %:([{axes}])` | ← Same |
| Specification | `$.({child})` | `$. %>({child})` | ← Same |
| Continuation | `$+({src}:{dest})%:[{axis}]` | `$+ %>({dest}) %<({src}) %:({axis})` | ← Same |
| Selection | *(not implemented)* | `$- %>({src}) %^(<selector>)` | ← Same |
| Group In | `&in` + value concepts | `&[{}] %>[{items}] %:({axis})` | `&[{}] %>[{items}] %+({axis})` ⭐ |
| Group Across | `&across({item}:{src})` | `&[#] %>({src}) %:({item})` | `&[#] %>[{items}] %+({axis})` ⭐ |
| If | `@if(<cond>)` | `@:' (<cond>)` | ← Same |
| If Not | `@if!(<cond>)` | `@:! (<cond>)` | ← Same |
| After | `@after({dep})` | `@. ({dep})` | ← Same |
| Every | `*every(...)%:[...]@(N)^[...]` | `*. %>(...) %<(...) %:(...) %^(...) %@(N)` | ← Same |

⭐ = Newer syntax using `%+` for explicit axis creation (recommended). Legacy `%:` syntax still supported.

---

## Practical Examples

### Example 1: Collecting Inputs

```ncd
{all inputs}
    <= &[{}] %>[{user query}, {system context}, {retrieved documents}]
    <- {user query}
    <- {system context}
    <- {retrieved documents}
```

**Effect**: Creates a labeled structure where each input is accessible by name.

---

### Example 2: Iterating Over Documents

```ncd
{all summaries}
    <= *. %>({documents}<$({document})*1>) %<({summary}) %:({document}) %@(1)
    <- {summary}
        <= ::(summarize this document)
        <- {document}*1
    <* {documents}
    <* {document}*1<*{documents}>
```

**Effect**: Loops through each document, generates a summary, collects all summaries.

---

### Example 3: Conditional Execution

```ncd
{final result}
    <= @:'(<validation passed>)
    <- {validated output}
        <= ::(validate the output)
        <- {draft output}
    <- <validation passed>
```

**Effect**: Only processes if validation passes.

---

### Example 4: Accumulating Results

```ncd
{updated total}
    <= $+ %>({current total}) %<({new value}) %:({values})
    <- {current total}
    <- {new value}
```

**Effect**: Appends new value to running total along the `values` axis.

---

## Design Rationale

### Why This Unified System?

1. **Consistency**: All operators use the same modifier vocabulary
2. **Language-agnostic**: No English words in formal representation
3. **Explicit roles**: Every data piece has a labeled role
4. **Extensible**: New modifiers can be added without breaking syntax
5. **Parseable**: All use `%X(...)` pattern for uniform extraction

### Modifier Mnemonics

- `%>` = **source** ("arrow pointing AT what we read")
- `%<` = **target** ("arrow pointing TO where we write")
- `%:` = **axis** (colon suggests "along this dimension")
- `%^` = **carry** (caret = "lift and carry forward")
- `%@` = **index** (at-sign = "at position N")
- `%+` = **create** (plus sign = "add a new dimension")

---

## Summary

| Operator Family | Operators | Purpose | Cost |
|----------------|-----------|---------|------|
| **Assigning ($)** | `$=`, `$%`, `$.`, `$+`, `$-` | Data routing and selection | Free |
| **Grouping (&)** | `&[{}]`, `&[#]` | Collection creation | Free |
| **Timing (@)** | `@:'`, `@:!`, `@.` | Execution control | Free |
| **Looping (*)** | `*.` | Iteration with state | Free |

**Key insight**: All syntactic operations are **free and deterministic**. They handle data plumbing so semantic operations (which cost tokens) receive exactly what they need.

---

## Next Steps

- **[References and Axes](references_and_axes.md)** - Understanding the tensor structure
- **[Complete Syntax Reference](complete_syntax_reference.md)** - Full formal grammar
- **[Execution Section](../3_execution/README.md)** - How operators work at runtime

---

## Quick Reference

### Operator Symbols
```
$   Assigning (data routing)
&   Grouping (collection)
@   Timing (execution control)
*   Looping (iteration)
```

### Modifiers
```
%>  Source (read from)
%<  Target (write to)
%:  Axis (dimension)
%^  Carry (state)
%@  Index (position)
%+  Create (new axis)
```

### Common Patterns
```
$= %>({alias})              # Merge concepts
&[{}] %>[{a}, {b}]         # Collect with labels
@:' (<condition>)           # Execute if true
*. %>(...) %:({axis})       # Iterate over axis
```

---

**Ready to understand References?** Continue to [References and Axes](references_and_axes.md).
