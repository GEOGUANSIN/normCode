# Serialize Dependency Tree to NCDS

## Task

Convert the dependency tree structure into **NormCode Draft Straightforward (.ncds)** text format. This is the final step of derivation, producing human-readable plan text.

## Input

- `input_1` — The tree structure with nodes, operations, and patterns (dependency tree)

---

## What is NCDS?

NCDS (NormCode Draft Straightforward) is the semi-formal, human-readable representation of a NormCode plan. It captures:
- Data dependencies (what produces what)
- Operations (transformations)
- Control flow (loops, conditions)

The `.ncds` file is later compiled to formal `.ncd` format.

---

## The Three Markers

From `derivation_v2.md`, every NCDS uses these three markers:

| Marker | Name | Meaning |
|--------|------|---------|
| `<-` | Value | "What data exists here?" — a concept (data) |
| `<=` | Function | "What operation produces it?" — an operation |
| `<*` | Context | "What controls or scopes this?" — loop base or condition |

**Writing direction**: Top-down (goal first, inputs later)
**Execution direction**: Bottom-up (inputs first, goal last)

---

## Semantic Concept Markers

Concepts are wrapped in type markers:

| Type | Marker | Example |
|------|--------|---------|
| Object (singular entity) | `{...}` | `{sentiment score}` |
| Collection (list/set) | `[...]` | `[all reviews]` |
| Condition (boolean) | `<...>` | `<is positive>` |

---

## Indentation Rules

- Each level of nesting = **4 spaces**
- Children are indented under their parent
- Comments use `/:` and align with their line
- The operation that produces a concept is its first child

```
<- {output}
    <= operation that produces it    /: 4 spaces in
    <- {input}                       /: 4 spaces in
        <= operation that produces input    /: 8 spaces in
        <- {deeper input}                   /: 8 spaces in
```

---

## Pattern Serialization

### Pattern 1: Linear Chain

**Tree**:
```
output
└── operation
    └── input
```

**NCDS**:
```ncds
<- {output}
    <= do the operation
    <- {input}
```

### Pattern 2: Multiple Inputs

**Tree**:
```
output
└── operation
    ├── input 1
    └── input 2
```

**NCDS**:
```ncds
<- {output}
    <= combine inputs
    <- {input 1}
    <- {input 2}
```

### Pattern 3: Iteration

**Tree**:
```
all results
└── for each item (iteration)
    ├── result (per-item)
    └── items [context]
```

**NCDS**:
```ncds
<- [all results]
    <= for each item in collection
        <= return processed item
        <- {processed item}
            <= process this item
            <- {current item}
    <- [items]
    <* {current item}
```

**Key elements**:
- `<- [all results]` — The aggregated collection
- `<= for each item` — The iteration operation (nested return)
- `<- [items]` — The collection being iterated
- `<* {current item}` — The loop variable (context marker)

### Pattern 4: Conditional

**Tree**:
```
result
└── gated operation
    ├── input
    └── condition [context]
```

**NCDS**:
```ncds
<- {result}
    <= do something
        <= if condition holds
        <* <condition>
    <- {input}
    <- <condition>
        <= check if something
        <- {data to check}
```

**Key elements**:
- The operation has a nested `<= if condition`
- `<* <condition>` marks what gates execution
- The condition itself is produced by a judgement operation

### Pattern 5: Grouping

**Tree**:
```
bundle
└── group operation
    ├── item 1
    ├── item 2
    └── item 3
```

**NCDS**:
```ncds
<- {bundle}
    <= bundle these items together
    <- {item 1}
    <- {item 2}
    <- {item 3}
```

### Pattern 6: Selection

**Tree**:
```
result
└── select operation
    ├── option 1
    └── option 2
```

**NCDS**:
```ncds
<- {result}
    <= select first available option
    <- {option 1}
    <- {option 2}
```

---

## Ground Concepts

Ground concepts (inputs with no producer) are declared with a comment:

```ncds
<- {ground concept}
    /: Ground: description of this input data
```

Or if already referenced as a child:
```ncds
<- {output}
    <= some operation
    <- {input data}    /: Ground
```

---

## Comments

Comments explain the plan:

```ncds
/: This is a top-level comment

<- {concept}
    <= operation    /: Inline comment
    
    /: Block comment explaining something
    <- {input}
```

---

## Serialization Algorithm

1. **Start from root**: Write the goal concept with `<-`
2. **Write producer**: If the concept has a producer operation, write it with `<=`
3. **Handle patterns**: Apply pattern-specific formatting (especially for iterations)
4. **Write children**: Recurse into each child with increased indent
5. **Mark context**: Use `<*` for loop bases and conditions
6. **Mark grounds**: Add `/: Ground:` comments for input concepts
7. **Add header**: Include a plan description at the top

---

## Output Format

```json
{
  "thinking": "Your serialization process",
  "ncds_content": "The complete .ncds file content as a string",
  "stats": {
    "line_count": 0,
    "concept_count": 0,
    "operation_count": 0,
    "ground_count": 0,
    "max_depth": 0
  }
}
```

---

## Complete Example

**Dependency Tree**:
```json
{
  "root": "summary report",
  "nodes": {
    "summary report": {
      "producer": "generate summary",
      "pattern": "multi_input",
      "children": ["all sentiments", "review count"]
    },
    "all sentiments": {
      "producer": "for each review",
      "pattern": "iteration",
      "children": ["sentiment"],
      "context": "reviews"
    },
    "sentiment": {
      "producer": "extract sentiment",
      "pattern": "linear",
      "children": ["current review"]
    },
    "current review": {
      "producer": null,
      "is_ground": false,
      "note": "loop variable"
    },
    "reviews": {
      "producer": null,
      "is_ground": true
    },
    "review count": {
      "producer": null,
      "is_ground": true
    }
  },
  "ground_concepts": ["reviews", "review count"]
}
```

**Serialized NCDS**:

```ncds
/: Review Sentiment Summarization
/: Analyzes customer reviews and produces a summary report

<- {summary report}
    <= generate a comprehensive summary report from all sentiment data
    <- [all sentiments]
        <= for each review in the collection
            <= return the extracted sentiment
            <- {sentiment}
                <= extract sentiment score from the review text
                <- {current review}
        <- [reviews]
            /: Ground: collection of customer reviews to analyze
        <* {current review}
    <- {review count}
        /: Ground: total number of reviews for statistics
```

**Stats**:
```json
{
  "stats": {
    "line_count": 16,
    "concept_count": 6,
    "operation_count": 4,
    "ground_count": 2,
    "max_depth": 4
  }
}
```

---

## Common Mistakes

| Mistake | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| Wrong indent (tabs vs spaces) | NCDS uses 4 spaces | Always use spaces |
| Missing context marker | Loops need `<*` | Always mark loop variable |
| Operation before concept | Concepts own operations | `<-` first, then `<=` as child |
| Forgetting ground comments | Makes plan harder to understand | Mark all inputs |
| Wrong type markers | Types matter semantically | `{}` object, `[]` collection, `<>` condition |

---

## Dependency Tree to Serialize

$input_1
