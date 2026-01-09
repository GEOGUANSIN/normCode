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

<<<<<<< HEAD
### Pattern 3: Iteration
=======
### Pattern 3: Iteration (with Return Operation)
>>>>>>> origin/dev

**Tree**:
```
all results
└── for each item (iteration)
<<<<<<< HEAD
    ├── result (per-item)
    └── items [context]
```

**NCDS**:
=======
    └── return item (return operation)
        └── result (per-item)
    └── items [input - GROUND]
    └── current item [context]
```

**NCDS** (when loop input is GROUND - no producer):
```ncds
<- [all results]
    <= for each item in collection
        <= return processed item              /: RETURN OPERATION (required!)
        /: Specifies what gets aggregated into [all results]
        
        <- {processed item}
            <= process this item
            <- {current item}
    <- [items]                                /: Ground collection (no producer)
        /: Ground: the input collection
    <* {current item}                         /: Loop context variable
```

**Key elements**:
- `<- [all results]` — The aggregated collection (output)
- `<= for each item` — The loop operator
- `<= return processed item` — **REQUIRED return operation** (what gets collected)
- `<- {processed item}` — The per-iteration result (nested under return)
- `<- [items]` — Ground collection input (**SIBLING of loop operator**)
- `<* {current item}` — The loop variable (**SIBLING of loop operator**)

**Note**: This pattern only applies when `[items]` is a GROUND concept (external input with no producer). See "Execution Order for Produced Loop Inputs" below for when the collection needs to be produced first.

**CRITICAL: Loop Input and Context Placement**

The loop input and context marker are **siblings of the LOOP OPERATOR**, at the same indentation level:

```ncds
<- [all results]                       /: 0 spaces
    <= for each item in collection     /: 4 spaces (child of all results)
        <= return processed item       /: 8 spaces (child of for each)
        <- {processed item}            /: 8 spaces
            <= process this item       /: 12 spaces
            <- {current item}          /: 12 spaces
    <- [items]                         /: 4 spaces (SIBLING of <= for each!)
    <* {current item}                  /: 4 spaces (SIBLING of <= for each!)
```

**WRONG** (do NOT do this):
>>>>>>> origin/dev
```ncds
<- [all results]
    <= for each item in collection
        <= return processed item
        <- {processed item}
            <= process this item
            <- {current item}
<<<<<<< HEAD
    <- [items]
    <* {current item}
```

**Key elements**:
- `<- [all results]` — The aggregated collection
- `<= for each item` — The iteration operation (nested return)
- `<- [items]` — The collection being iterated
- `<* {current item}` — The loop variable (context marker)

### Pattern 4: Conditional
=======
        <- [items]                     /: WRONG - 8 spaces, nested under loop!
        <* {current item}              /: WRONG - 8 spaces, nested under loop!
```

**Rule**: Loop inputs and context markers are **siblings of the loop operator** (same indentation), NOT nested inside the loop body.

**CRITICAL: Execution Order for Produced Loop Inputs**

If the loop input **needs to be produced by an operation** (e.g., parsing a file), its producer must be defined at a **higher level** so it executes BEFORE the loop starts.

**Why?** The flow index system processes children before parents. If you define the producer as sibling of the loop operator, it gets a flow index that might execute AFTER the loop tries to start.

**Correct Pattern** (when loop input has a producer):

```ncds
<- {final output}                          /: Root
    <= produce final output
    
    /: PHASE 1: Prepare the collection (executes FIRST)
    <- [items]                             /: Sibling of loop output - flow 1.1
        <= parse source into items
        <- {source}
    
    /: PHASE 2: Process each item (executes SECOND)
    <- [processed items]                   /: Sibling of items - flow 1.2
        <= for each item in collection
            <= return processed item
            <- {processed item}
                <= process this item
                <- {current item}
        <- [items]                         /: REFERENCE ONLY - no producer here!
        <* {current item}
```

**Key insight**:
1. `[items]` is DEFINED (with producer `<= parse`) at flow `1.1`
2. `[processed items]` loop is at flow `1.2` — executes AFTER `1.1` is done
3. Inside the loop, `<- [items]` is just a REFERENCE (no producer), not a definition

**WRONG** (producer inside loop scope):

```ncds
<- [processed items]
    <= for each item in collection
        <= return processed item
        <- {processed item}
            <= process this item
            <- {current item}
    <- [items]                             /: WRONG - producer is here!
        <= parse source into items         /: This executes TOO LATE!
        <- {source}
    <* {current item}
```

This is wrong because:
- `[items]` has flow `1.1.2` (inside loop scope)
- The loop at `1.1.1` will try to execute before `1.1.2` is ready!

**Rule**: If a loop input needs to be produced, define it (with producer) as a **sibling of the loop output**, not inside the loop's scope. Inside the loop, just reference it.

### Pattern 4: Conditional (Single Timing Gate)
>>>>>>> origin/dev

**Tree**:
```
result
└── gated operation
<<<<<<< HEAD
    ├── input
    └── condition [context]
=======
    └── timing gate
    └── condition [context]
    └── input
>>>>>>> origin/dev
```

**NCDS**:
```ncds
<- {result}
    <= do something
<<<<<<< HEAD
        <= if condition holds
        <* <condition>
=======
        <= when condition holds          /: TIMING GATE (child of operation)
        <* <condition>                    /: Context: what the gate checks
>>>>>>> origin/dev
    <- {input}
    <- <condition>
        <= check if something
        <- {data to check}
```

**Key elements**:
<<<<<<< HEAD
- The operation has a nested `<= if condition`
- `<* <condition>` marks what gates execution
=======
- The operation has a nested timing gate: `<= when condition holds`
- `<* <condition>` marks what gates execution (under the timing gate)
>>>>>>> origin/dev
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

<<<<<<< HEAD
### Pattern 6: Selection
=======
### Pattern 6: Selection (Multiple Timing-Gated Options)

**CRITICAL**: Selection with "if X then do A, if Y then do B" patterns requires:
1. **First**: Judgement (produces the type/category to check)
2. **Second**: Condition checks (one boolean per option)
3. **Third**: Gated options (each with timing gate referencing its condition)
>>>>>>> origin/dev

**Tree**:
```
result
<<<<<<< HEAD
└── select operation
    ├── option 1
    └── option 2
=======
└── select first valid
    ├── type (from judgement)
    ├── is A (condition)
    ├── is B (condition)
    ├── option A (gated)
    └── option B (gated)
>>>>>>> origin/dev
```

**NCDS**:
```ncds
<- {result}
<<<<<<< HEAD
    <= select first available option
    <- {option 1}
    <- {option 2}
```

=======
    <= select first valid option
    
    /: STEP 1: Judge the type (executed FIRST)
    <- {type}
        <= judge what type this is
        <- {input}
    
    /: STEP 2: Check conditions (executed SECOND)
    <- <is type A>
        <= check if type equals A
        <- {type}
    
    <- <is type B>
        <= check if type equals B
        <- {type}
    
    /: STEP 3: Apply matching operation (executed THIRD, timing-gated)
    <- {option A result}
        <= do operation A
            <= when condition holds       /: TIMING GATE
            <* <is type A>
        <- {input}
    
    <- {option B result}
        <= do operation B
            <= when condition holds       /: TIMING GATE
            <* <is type B>
        <- {input}
```

**Key principles**:
- **One-inference-only**: Each value concept has exactly ONE producing operation
- **First-executed, first-written**: Conditions before gated options
- **Timing gates are children**: `<= when condition holds` is a child of the operation, not a sibling
- **Context marks the condition**: `<* <is type A>` under the timing gate

>>>>>>> origin/dev
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
<<<<<<< HEAD
3. **Handle patterns**: Apply pattern-specific formatting (especially for iterations)
4. **Write children**: Recurse into each child with increased indent
5. **Mark context**: Use `<*` for loop bases and conditions
6. **Mark grounds**: Add `/: Ground:` comments for input concepts
7. **Add header**: Include a plan description at the top

=======
3. **Handle patterns**: Apply pattern-specific formatting
4. **Write children**: Recurse into each child with increased indent
5. **Handle iteration context specially**: See below
6. **Mark grounds**: Add `/: Ground:` comments for input concepts
7. **Add header**: Include a plan description at the top

### Special Handling for Iterations

When the tree has a node with `pattern: "iteration"`:
- The tree's `children` array contains the per-item result
- The tree's `context` field contains the collection name

**Two cases for loop input placement**:

**Case A: Loop input is a ground concept (no producer)**
- Place it as sibling of the loop operator
- Reference only (no producer to write)

**Case B: Loop input has a producer (needs to be computed)**
- Define it (with producer) as **sibling of the loop OUTPUT** (at parent level)
- Inside loop scope, only reference it (without producer)
- This ensures it executes BEFORE the loop starts

**For serialization (Case B - most common)**:
1. At PARENT level: Write the collection WITH its producer (executes first)
2. At PARENT level: Write the aggregated output (`<- [output]`)
3. Write the loop operator (`<= for each`) — child of output
4. Write the return operation (`<= return`) — child of loop
5. Write the per-item result and its tree — child of return
6. Write the collection REFERENCE (`<- [collection]`, no producer) — sibling of loop
7. Write the context marker (`<* {item}`) — sibling of loop

**Correct structure** (loop input has producer):

```ncds
<- {root output}                              /: 0 spaces
    <= produce root output
    
    <- [collection]                           /: 4 spaces - DEFINED here (with producer)
        <= parse/produce collection           /: 8 spaces - EXECUTES FIRST
        <- {source}
    
    <- [processed items]                      /: 4 spaces - Loop output (sibling of collection)
        <= for each item in collection        /: 8 spaces - Loop operator
            <= return processed item          /: 12 spaces - Return operation
            <- {per-item result}              /: 12 spaces - What gets returned
                <= process item               /: 16 spaces - Processing
                <- {current item}             /: 16 spaces - Loop variable ref
        <- [collection]                       /: 8 spaces - REFERENCE only (no producer)
        <* {current item}                     /: 8 spaces - Context marker
```

**Key rules**:
1. If loop input has a producer, DEFINE it at the same level as the loop output
2. Inside the loop scope, only REFERENCE the collection (no producer)
3. This ensures correct flow index ordering: collection produces BEFORE loop executes

>>>>>>> origin/dev
---

## Output Format

```json
{
  "thinking": "Your serialization process - explain your approach",
  "result": "The complete .ncds file content as a string (the actual NCDS text)"
}
```

**Important**: The `result` field should contain ONLY the NCDS text content, ready to be written to a `.ncds` file. Do NOT include stats or metadata in the result.

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

<<<<<<< HEAD
=======
## The One-Inference-Only Principle

**CRITICAL RULE**: Each value concept must have **exactly one** producing operation.

**WRONG** (multiple operations for same value):
```ncds
<= select first valid
    <= formalize as object         ← operation under operation - WRONG!
        <- {result}
            <= formalize as object ← another operation for same value - VIOLATION!
```

**CORRECT** (one operation per value):
```ncds
<- {result}
    <= select first valid option
    <- {option A result}
        <= formalize as object     ← single operation producing this value
```

---

## Ordering Principle: First-Executed, First-Written

Within any scope, write concepts in execution order:

| Scope | Order |
|-------|-------|
| **Under root** | Ground concepts → Phase 1 → Phase 2 → Phase 3 |
| **Within a selection** | Judgement → Condition checks → Gated options |
| **Within a loop** | Return operation → Loop body → Loop input → Context (`<*`) |

**Why this matters**: The orchestrator assigns flow indices based on position. If conditions come AFTER gated options, the timing gate will try to check a condition that hasn't been evaluated yet.

---

>>>>>>> origin/dev
## Common Mistakes

| Mistake | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| Wrong indent (tabs vs spaces) | NCDS uses 4 spaces | Always use spaces |
| Missing context marker | Loops need `<*` | Always mark loop variable |
| Operation before concept | Concepts own operations | `<-` first, then `<=` as child |
| Forgetting ground comments | Makes plan harder to understand | Mark all inputs |
| Wrong type markers | Types matter semantically | `{}` object, `[]` collection, `<>` condition |
<<<<<<< HEAD
=======
| **Multiple operations per value** | One-inference-only violated | Each `<-` has exactly one `<=` as child |
| **Nested operations** | `<=` under `<=` without value | Operations must produce values |
| **Wrong order in selection** | Conditions after options | Write: judgement → conditions → options |
| **Missing return operation** | Looper doesn't know what to collect | Always include `<= return...` in loops |
| **Timing gate as sibling** | Gate must be child of operation | `<= when...` is child of `<= operation` |
>>>>>>> origin/dev

---

## Dependency Tree to Serialize

$input_1
