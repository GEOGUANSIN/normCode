# Formalization

**Phase 2: Adding structural rigor—flow indices, sequence types, and bindings.**

---

## Overview

**Formalization** is the second phase of NormCode compilation. It transforms the draft `.ncds` format into rigorous `.ncd` (NormCode Draft) with complete structural annotations.

**Input**: `.ncds` (draft straightforward)  
**Output**: `.ncd` (formal) with flow indices and sequence types

**Core Task**: Remove ambiguity by adding explicit structural metadata.

---

## What Formalization Adds

### The Four Key Additions

| Addition | Purpose | Example |
|----------|---------|---------|
| **Flow Indices** | Unique addresses for each step | `?{flow_index}: 1.2.3` |
| **Sequence Types** | Operation classification | `?{sequence}: imperative` |
| **Semantic Types** | Concept classification | `{}`, `[]`, `<>`, `::()`, etc. |
| **Value Bindings** | Input ordering | `<:{1}>`, `<:{2}>`, `<:{3}>` |

---

## Flow Indices

### Purpose

**Flow indices** are hierarchical addresses that uniquely identify every step in the plan.

**Format**: `1.2.3.4...` where each number is a level in the tree.

### Generation Rules

1. **Start at root**: Root concept gets `1`
2. **Increment within level**: Siblings get sequential numbers
3. **Nest for children**: Children append `.1`, `.2`, `.3`, etc.
4. **All concept lines get indices**: Including `<=`, `<-`, `<*`, and `:<:`

### Example

**Input (`.ncds`)**:
```ncds
<- result
    <= calculate
    <- input A
        <= process A
        <- raw A
    <- input B
        <= process B
        <- raw B
```

**Output (`.ncd` with flow indices)**:
```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(calculate) | ?{flow_index}: 1.1
    <- {input A} | ?{flow_index}: 1.2
        <= ::(process A) | ?{flow_index}: 1.2.1
        <- {raw A} | ?{flow_index}: 1.2.1.1
    <- {input B} | ?{flow_index}: 1.3
        <= ::(process B) | ?{flow_index}: 1.3.1
        <- {raw B} | ?{flow_index}: 1.3.1.1
```

### Reading Flow Indices

**`1.2.3` means**:
- `1` - First root concept
- `.2` - Second child of root
- `.3` - Third child of that concept

**Properties**:
- **Unique**: Each step has exactly one flow index
- **Hierarchical**: Parent-child relationships are clear
- **Ordered**: Execution can follow index order (with dependency resolution)

### Why Flow Indices Matter

| Use Case | How Flow Indices Help |
|----------|---------------------|
| **Debugging** | "Step 1.3.2 failed" tells you exactly where |
| **Checkpointing** | Resume from specific index |
| **Cross-referencing** | Reference other steps explicitly |
| **Dependency tracking** | Orchestrator knows execution order |
| **Logging** | Detailed execution traces |

### Deprecated Pattern

> **Note**: Older NormCode versions marked flow_index only on functional concepts (`<=`). Current practice marks **every concept line** for complete traceability.

**Old (deprecated)**:
```ncd
:<:{result}
    <= ::(calculate) | ?{flow_index}: 1
    <- {input}
```

**New (current)**:
```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(calculate) | ?{flow_index}: 1.1
    <- {input} | ?{flow_index}: 1.2
```

---

## Sequence Types

### Purpose

**Sequence types** classify operations to determine execution strategy.

### The Two Categories

```
┌─────────────────────────────────────────────────┐
│  SEMANTIC SEQUENCES                              │
│  → CREATE information via LLM/tools              │
│  → Expensive (tokens), non-deterministic         │
│  → imperative, judgement                        │
├─────────────────────────────────────────────────┤
│  SYNTACTIC SEQUENCES                             │
│  → RESHAPE information via tensor algebra        │
│  → Free, deterministic, auditable               │
│  → assigning, grouping, timing, looping         │
└─────────────────────────────────────────────────┘
```

### Sequence Type Detection

**Rule**: Analyze the functional concept syntax to determine sequence type.

| Functional Concept Pattern | Sequence Type | Category |
|----------------------------|---------------|----------|
| `::()` or `({})` | `imperative` | Semantic |
| `::<>` or `<{}>` | `judgement` | Semantic |
| `$=`, `$.`, `$+`, `$-`, `$%` | `assigning` | Syntactic |
| `&[{}]`, `&[#]` | `grouping` | Syntactic |
| `@:'`, `@:!`, `@.` | `timing` | Syntactic |
| `*.` | `looping` | Syntactic |

**Priority**: Check for syntactic operators FIRST (more specific), then fall back to semantic patterns.

### Example

**Input (`.ncds`)**:
```ncds
<- result
    <= calculate sum
    <- numbers
        <= collect all numbers
        <- number A
        <- number B
```

**Output (`.ncd` with sequences)**:
```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(calculate sum) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {numbers} | ?{flow_index}: 1.2
        <= &[#] | ?{flow_index}: 1.2.1 | ?{sequence}: grouping
        <- {number A} | ?{flow_index}: 1.2.1.1
        <- {number B} | ?{flow_index}: 1.2.1.2
```

**Explanation**:
- `calculate sum` → `imperative` (semantic operation, calls LLM)
- `collect all numbers` → Recognized as grouping, transformed to `&[#]` → `grouping` sequence

### Implicit Operator Recognition

Formalization can **recognize natural language patterns** and convert them to operators:

| NL Pattern | Recognized As | Operator |
|------------|---------------|----------|
| "collect all X" | Grouping | `&[#]` |
| "combine X and Y" | Grouping | `&[{}]` |
| "for each X" | Looping | `*.` |
| "if condition" | Timing | `@:'` |
| "select first valid" | Assigning | `$.` |

---

## Semantic Types

### Purpose

**Semantic types** classify concepts by their nature (object, relation, proposition, etc.).

### The Type System

| Symbol | Type | Description | Examples |
|--------|------|-------------|----------|
| `{}` | Object | Singular entity | `{document}`, `{result}` |
| `[]` | Relation | Collection | `[numbers]`, `[files]` |
| `<>` | Proposition | Boolean state | `<is valid>`, `<ready>` |
| `:S:` | Subject | Agent/actor | `:LLM:`, `:Agent:` |
| `::()` | Imperative | Command/action | `::(calculate)` |
| `::<>` | Judgement | Evaluation | `::(is valid)<ALL True>` |

### Type Inference Rules

**For value concepts** (`<-`):

1. **Singular nouns** → `{}` (Object)
   - "document", "result", "value"
2. **Plural nouns or "all X"** → `[]` (Relation)
   - "documents", "all numbers", "files"
3. **Boolean/state phrases** → `<>` (Proposition)
   - "is valid", "passed", "ready"

**For functional concepts** (`<=`):

1. **Action verbs** → `::()` (Imperative)
   - "calculate", "extract", "process"
2. **Evaluation phrases** → `::<>` (Judgement)
   - "is valid", "meets criteria", "passes test"
3. **Syntactic operators** → Keep operator syntax
   - `$.`, `&[{}]`, `@:'`, `*.`

### Example

**Input (`.ncds`)**:
```ncds
<- validation result
    <= check if input is valid
    <- input data
```

**Output (`.ncd` with types)**:
```ncd
:<:{validation result} | ?{flow_index}: 1
    <= ::(check if input is valid)<ALL True> | ?{flow_index}: 1.1 | ?{sequence}: judgement
    <- {input data} | ?{flow_index}: 1.2
```

**Explanation**:
- `validation result` → `{}` (singular object)
- `check if input is valid` → Recognized as judgement, gets `::<>` and truth assertion
- `input data` → `{}` (singular object)

---

## Value Bindings

### Purpose

**Value bindings** explicitly order multi-input operations to remove ambiguity.

### The Problem

**Ambiguous**:
```ncd
<= ::(divide A and B)
<- {number A}
<- {number B}
```

**Question**: Which is dividend and which is divisor?

### The Solution: Value Placement

**Syntax**: `<:{N}>` on value concepts

**Example**:
```ncd
<= ::(divide {1} by {2})
<- {number A}<:{1}>
<- {number B}<:{2}>
```

**Now clear**: A is {1} (dividend), B is {2} (divisor)

### Extraction and Assignment

**During formalization**:

1. **Scan functional concept** for placeholders: `{1}`, `{2}`, `{3}`, etc.
2. **Match with value concepts** in order
3. **Add bindings** `<:{N}>` to value concepts

**Example**:

**Input (`.ncds`)**:
```ncds
<- result
    <= sum A and B to get result
    <- number A
    <- number B
    <- result placeholder
```

**Formalization detects** "A and B to get result" pattern:

**Output (`.ncd`)**:
```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(sum {1} and {2} to get {3}) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {number A}<:{1}> | ?{flow_index}: 1.2
    <- {number B}<:{2}> | ?{flow_index}: 1.3
    <- {result}<:{3}> | ?{flow_index}: 1.4
```

### Advanced Binding: Instance Markers

**For more complex references**:

| Marker | Purpose | Example |
|--------|---------|---------|
| `<$()%>` | Instance marker (in functional concepts) | `{1}<$({input})%>` |
| `<$()=>` | Identifier marker | `{result}<$({version})=>` |

See [Grammar/Complete Syntax Reference](../2_grammar/complete_syntax_reference.md) for details.

---

## Root Concept Marker

### The `:<:` Marker

The **root concept** (final output) uses special marker `:<:`:

**Before formalization**:
```ncds
<- final result
    <= compute
    <- input
```

**After formalization**:
```ncd
:<:{final result} | ?{flow_index}: 1
    <= ::(compute) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {input} | ?{flow_index}: 1.2
```

**Purpose**:
- Marks the top-level goal
- Identifies the final output
- Used by orchestrator to know what to return

---

## Complete Formalization Example

### Before: `.ncds`

```ncds
<- investment decision
    <= synthesize recommendation
    <- risk analysis
        <= analyze risk
        <- price data
        <= validate signals
        <- market signals
    <- sentiment score
        <= analyze sentiment
        <- news articles
```

### After: `.ncd`

```ncd
:<:{investment decision} | ?{flow_index}: 1
    <= ::(synthesize recommendation from {1} and {2}) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {risk analysis}<:{1}> | ?{flow_index}: 1.2
        <= ::(analyze risk based on {1} given {2}) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
        <- {price data}<:{1}> | ?{flow_index}: 1.2.2
        <- <signals validated><:{2}> | ?{flow_index}: 1.2.3
            <= ::(validate signals)<ALL True> | ?{flow_index}: 1.2.3.1 | ?{sequence}: judgement
            <- {market signals} | ?{flow_index}: 1.2.3.1.1
    <- {sentiment score}<:{2}> | ?{flow_index}: 1.3
        <= ::(analyze sentiment) | ?{flow_index}: 1.3.1 | ?{sequence}: imperative
        <- {news articles} | ?{flow_index}: 1.3.1.1
```

### What Changed

1. ✅ Flow indices on every line
2. ✅ Sequence types determined
3. ✅ Semantic types added (`{}`, `<>`, `::()`, `::<>`)
4. ✅ Value bindings added (`<:{1}>`, `<:{2}>`)
5. ✅ Root marked with `:<:`
6. ✅ Truth assertion added to judgement (`<ALL True>`)

---

## Formalization Rules Summary

### Flow Index Assignment

```
1. Start at 1 for root
2. First child: append .1
3. Sibling: increment last digit
4. Grandchild: append another level
```

### Sequence Type Assignment

```
1. Check for syntactic operators ($, &, @, *)
2. If none, check semantic patterns (::(), ::<>)
3. Assign appropriate sequence type
4. Add to ?{sequence}: comment
```

### Semantic Type Assignment

```
1. Analyze concept name (singular/plural/boolean)
2. Assign {} for objects, [] for relations, <> for propositions
3. For functional concepts, use ::() or ::<>
4. Add truth assertions to judgements
```

### Value Binding Assignment

```
1. Scan functional concept for placeholders
2. Match placeholders to value concepts in order
3. Add <:{N}> markers to value concepts
4. Ensure consistency
```

---

## Validation After Formalization

### Checklist

Before moving to post-formalization:

**Structure**:
- [ ] All lines have flow indices
- [ ] Flow indices are unique
- [ ] Flow indices follow hierarchical pattern
- [ ] Root has `:<:` marker

**Sequences**:
- [ ] All functional concepts have sequence types
- [ ] Sequence types are valid
- [ ] Syntactic operators correctly recognized
- [ ] Judgements have truth assertions

**Types**:
- [ ] All concepts have semantic types
- [ ] Types match concept nature
- [ ] Functional concepts use `::()` or `::<>`
- [ ] Collections use `[]`

**Bindings**:
- [ ] Multi-input operations have value bindings
- [ ] Binding numbers are sequential (1, 2, 3...)
- [ ] All placeholders are matched

### Common Errors

| Error | Symptom | Fix |
|-------|---------|-----|
| **Duplicate flow index** | Two lines have same index | Re-run index assignment |
| **Missing sequence type** | Functional concept without `?{sequence}:` | Add sequence determination |
| **Wrong type** | Collection marked as `{}` instead of `[]` | Fix type inference |
| **Missing bindings** | Multi-input operation without `<:{N}>` | Add value placements |
| **Inconsistent indentation** | Flow indices don't match depth | Fix indentation or indices |

---

## Formalization Tools

### Automated Formalization

**Command**:
```bash
python compiler.py formalize draft.ncds
```

**Output**: `draft.ncd` with all formalizations applied

### Manual Formalization

**Steps**:
1. Copy `.ncds` content
2. Add flow indices (start at 1, follow rules)
3. Determine sequence types for each `<=`
4. Add semantic types to concepts
5. Add value bindings where needed
6. Mark root with `:<:`
7. Validate with checklist

### Editor Support

The NormCode editor can assist:
- Auto-assign flow indices
- Suggest sequence types
- Validate syntax
- Preview formalized output

See [Editor](editor.md) for details.

---

## Formalization vs. Post-Formalization

### What Formalization Does

- ✅ Adds flow indices
- ✅ Determines sequence types
- ✅ Assigns semantic types
- ✅ Creates value bindings
- ✅ Marks root concept

### What Formalization Does NOT Do

- ❌ Add paradigm configurations (that's Post-Formalization)
- ❌ Link to resources (that's Post-Formalization)
- ❌ Specify axes and shapes (that's Post-Formalization)
- ❌ Generate working_interpretation (that's Activation)

**Formalization focuses on STRUCTURE, not EXECUTION.**

---

## Next Steps

After formalization, your `.ncd` file moves to:

- **[Post-Formalization](post_formalization.md)** - Add norms, resources, and execution configuration

---

## Summary

### Key Takeaways

| Concept | Insight |
|---------|---------|
| **Flow indices** | Unique hierarchical addresses for every step |
| **Sequence types** | Classify operations as semantic (LLM) or syntactic (free) |
| **Semantic types** | Classify concepts by nature (object, relation, proposition) |
| **Value bindings** | Remove ambiguity in multi-input operations |
| **Automated** | Tools handle formalization automatically |

### The Formalization Promise

**Formalization removes ambiguity**:

1. Vague `.ncds` becomes precise `.ncd`
2. Every step has unique identity
3. Execution strategy is clear
4. Data flow is explicit
5. Ready for configuration

**Result**: A plan with rigorous structure, ready for execution configuration.

---

**Ready to configure execution?** Continue to [Post-Formalization](post_formalization.md) to enrich your plan with norms and resources.
