# Classify Operation Pattern

## Task

Determine the **pattern type** for a specific operation based on its context. This classification determines how the operation will be structured in the final plan.

## Inputs

- `input_1` — The operation to classify (current operation)
- `input_2` — Gathered context about this operation (operation context)

---

## Pattern Types

### Semantic Patterns (Require LLM or Complex Logic)

These patterns involve actual computation or reasoning:

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **linear** | Single input → single output | Simple transformation, extraction, generation |
| **multi_input** | Multiple inputs → single output | Combining, synthesizing, merging |
| **judgement** | Any inputs → boolean output | Checks, validations, evaluations |

### Syntactic Patterns (Control Flow)

These patterns control execution flow, not actual computation:

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **iteration** | Process each item in collection | "for each", "process all" |
| **conditional** | Execute if condition is true | "if X then", gated execution |
| **selection** | Pick first valid from options | "choose first", "prefer X else Y" |
| **grouping** | Bundle items together | "collect", "bundle", "combine" |

---

## Classification Decision Tree

```
1. Does it produce a boolean/condition?
   YES → judgement
   NO  → continue

2. Does it iterate over a collection?
   YES → iteration
   NO  → continue

3. Is it gated by a condition?
   YES → conditional
   NO  → continue

4. Does it select from multiple options?
   YES → selection
   NO  → continue

5. Does it bundle/collect items?
   YES → grouping
   NO  → continue

6. How many inputs?
   Multiple → multi_input
   Single   → linear
```

---

## Pattern Details

### Linear
- **Inputs**: Single concept
- **Output**: Single concept
- **Execution**: LLM or Script depending on operation
- **Example**: "extract sentiment from review" (1 input → 1 output)

### Multi-Input
- **Inputs**: Two or more concepts
- **Output**: Single concept
- **Execution**: LLM or Script
- **Example**: "generate report from count and reviews" (2 inputs → 1 output)

### Judgement
- **Inputs**: Any number
- **Output**: Boolean/condition
- **Execution**: LLM (subjective) or Script (exact comparison)
- **Example**: "check if score > 0.7" → produces true/false

### Iteration
- **Inputs**: Collection
- **Output**: Per-item result (aggregated)
- **Execution**: Control flow (orchestrator handles)
- **Example**: "for each review in reviews"

### Conditional
- **Inputs**: Condition + data
- **Output**: Gated result
- **Execution**: Control flow
- **Example**: "if positive then add to list"

### Selection
- **Inputs**: Multiple options
- **Output**: First valid option
- **Execution**: Control flow
- **Example**: "use cached value if available, else compute"

### Grouping
- **Inputs**: Multiple items
- **Output**: Bundled structure
- **Execution**: Control flow
- **Example**: "bundle results and errors into report"

---

## Semantic vs Syntactic

| Semantic (actual work) | Syntactic (control flow) |
|------------------------|--------------------------|
| linear | iteration |
| multi_input | conditional |
| judgement | selection |
| | grouping |

**Semantic** patterns invoke LLM or scripts to do real computation.
**Syntactic** patterns are handled by the orchestrator for control flow.

---

## Output Format

```json
{
  "thinking": "Your classification reasoning using the decision tree",
  "classification": {
    "pattern": "linear" | "multi_input" | "judgement" | "iteration" | "conditional" | "selection" | "grouping",
    "category": "semantic" | "syntactic",
    "execution": "llm" | "script" | "orchestrator",
    "input_count": 0,
    "output_type": "object" | "collection" | "condition",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this pattern"
  }
}
```

---

## Examples

### Example 1: Linear Pattern

**Operation**: "extract sentiment score"  
**Context**: 1 input (review), produces object (sentiment score), inside loop, uses LLM

```json
{
  "thinking": "Produces object (not boolean) → not judgement. Not iterating itself. Not conditional. Not selecting. Not grouping. Single input → linear.",
  "classification": {
    "pattern": "linear",
    "category": "semantic",
    "execution": "llm",
    "input_count": 1,
    "output_type": "object",
    "confidence": 0.95,
    "reasoning": "Single input transformation using LLM extraction"
  }
}
```

### Example 2: Judgement Pattern

**Operation**: "check if score is positive"  
**Context**: 1 input (sentiment score), produces condition (is positive), exact comparison

```json
{
  "thinking": "Produces boolean/condition → judgement. Exact numeric comparison (> 0.7) → script.",
  "classification": {
    "pattern": "judgement",
    "category": "semantic",
    "execution": "script",
    "input_count": 1,
    "output_type": "condition",
    "confidence": 0.95,
    "reasoning": "Produces boolean via exact numeric comparison"
  }
}
```

### Example 3: Iteration Pattern

**Operation**: "iterate over reviews"  
**Context**: 1 input (reviews collection), produces loop variable

```json
{
  "thinking": "Iterates over collection → iteration. Control flow handled by orchestrator.",
  "classification": {
    "pattern": "iteration",
    "category": "syntactic",
    "execution": "orchestrator",
    "input_count": 1,
    "output_type": "object",
    "confidence": 0.95,
    "reasoning": "For-each loop over collection"
  }
}
```

### Example 4: Conditional Pattern

**Operation**: "add review to positive reviews if positive"  
**Context**: 2 inputs (review, is_positive condition), gated by condition

```json
{
  "thinking": "Execution gated by 'is positive' condition → conditional.",
  "classification": {
    "pattern": "conditional",
    "category": "syntactic",
    "execution": "orchestrator",
    "input_count": 2,
    "output_type": "collection",
    "confidence": 0.90,
    "reasoning": "Append operation gated by boolean condition"
  }
}
```

### Example 5: Multi-Input Pattern

**Operation**: "generate summary report"  
**Context**: 2 inputs (count, positive reviews), produces object

```json
{
  "thinking": "Multiple inputs (count, reviews) combined → multi_input. Uses LLM for generation.",
  "classification": {
    "pattern": "multi_input",
    "category": "semantic",
    "execution": "llm",
    "input_count": 2,
    "output_type": "object",
    "confidence": 0.95,
    "reasoning": "Synthesizes multiple inputs into report using LLM"
  }
}
```

---

## Now Classify

### Operation
$input_1

### Context
$input_2
