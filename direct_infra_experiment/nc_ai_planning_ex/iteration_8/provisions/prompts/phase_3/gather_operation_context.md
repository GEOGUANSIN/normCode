# Gather Operation Context

## Task

For a specific operation, gather all relevant context from the extraction data to prepare for pattern classification.

## Inputs

- `input_1` — The operation to analyze (current operation)
- `input_2` — Full extraction results (extraction data)

---

## What Context to Gather

### 1. Data Flow
- **Inputs**: What concepts does this operation consume?
- **Output**: What concept does this operation produce?
- **Input count**: Single input or multiple inputs?

### 2. Position in Execution
- **Upstream**: What operations must complete before this?
- **Downstream**: What operations depend on this?
- **Is root producer**: Does it produce the final output?
- **Is leaf consumer**: Does it only consume inputs (no upstream ops)?

### 3. Control Flow Context
- **Inside loop?**: Is this operation executed per-iteration?
- **Loop base**: If inside loop, what collection is being iterated?
<<<<<<< HEAD
- **Is conditional?**: Is execution gated by a condition?
- **Condition**: If conditional, what condition gates it?
=======
- **Is conditional?**: Is execution gated by a single condition?
- **Condition**: If conditional, what condition gates it?
- **Is selection?**: Does this choose between multiple options based on conditions?
- **Selection options**: If selection, what are the possible options?
- **Discriminator**: If selection, what determines which option is chosen?
>>>>>>> origin/dev

### 4. Operation Characteristics
- **Produces boolean?**: Does output look like a true/false check?
- **Is aggregation?**: Does it collect/bundle multiple items?
- **Is iteration?**: Does it process a collection per-item?
- **Execution type**: LLM (reasoning/generation) or Script (computation)?

---

## How to Extract from Extraction Data

The extraction data contains:
- `concepts`: List of all concepts with types and roles
- `operations`: List of all operations with categories
- `dependencies`: Relationships between concepts/operations
- `patterns`: Identified control patterns (loops, conditionals)

**For the current operation, find**:
1. Dependencies where this operation is the target → these are inputs
2. Dependencies where this operation is the source → this is output
3. Patterns that mention this operation → control flow context

---

## Output Format

```json
{
  "thinking": "Your context gathering process",
  "result": {
    "operation": "the operation name",
    "inputs": {
      "concepts": ["input concept names"],
      "count": 0
    },
    "output": {
      "concept": "output concept name",
      "type": "object | collection | condition"
    },
    "position": {
      "upstream_operations": ["operations before this"],
      "downstream_operations": ["operations after this"],
      "is_root_producer": true | false,
      "is_leaf_consumer": true | false
    },
    "control_flow": {
      "inside_loop": true | false,
      "loop_collection": "collection being iterated (if applicable)",
      "is_conditional": true | false,
<<<<<<< HEAD
      "condition": "condition gating execution (if applicable)"
=======
      "condition": "condition gating execution (if applicable)",
      "is_selection": true | false,
      "selection_options": ["list of option operations (if applicable)"],
      "discriminator": "concept that determines selection (if applicable)"
>>>>>>> origin/dev
    },
    "characteristics": {
      "produces_boolean": true | false,
      "is_aggregation": true | false,
      "is_iteration": true | false,
      "execution_type": "llm | script"
    }
  }
}
```

**Important**: Put the context in the `result` field. The `thinking` field is for your reasoning only.

---

## Example

**Operation**: "extract sentiment score"

**Extraction Data** (summary):
- Concepts: reviews (collection, input), review (object, loop_var), sentiment score (object, intermediate), is positive (condition), positive reviews (collection), report (object, output)
- Operations: iterate over reviews, extract sentiment score, check if positive, add to positive reviews, generate report
- Dependencies: extract sentiment ← needs ← review; extract sentiment → produces → sentiment score
- Patterns: iteration (for each review), conditional (if positive)

**Context Gathered**:

```json
{
  "thinking": "Looking at dependencies: 'extract sentiment' needs 'review' (1 input) and produces 'sentiment score' (object). It's inside the 'iterate over reviews' loop. Not conditional itself. Downstream: 'check if positive' uses its output. Uses LLM for semantic extraction.",
  "result": {
    "operation": "extract sentiment score",
    "inputs": {
      "concepts": ["review"],
      "count": 1
    },
    "output": {
      "concept": "sentiment score",
      "type": "object"
    },
    "position": {
      "upstream_operations": ["iterate over reviews"],
      "downstream_operations": ["check if positive"],
      "is_root_producer": false,
      "is_leaf_consumer": false
    },
    "control_flow": {
      "inside_loop": true,
      "loop_collection": "reviews",
      "is_conditional": false,
      "condition": null
    },
    "characteristics": {
      "produces_boolean": false,
      "is_aggregation": false,
      "is_iteration": false,
      "execution_type": "llm"
    }
  }
}
```

---

## Now Gather Context

### Current Operation
$input_1

### Extraction Data
$input_2
