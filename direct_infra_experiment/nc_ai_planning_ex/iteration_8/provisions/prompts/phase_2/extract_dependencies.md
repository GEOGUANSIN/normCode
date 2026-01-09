# Extract Dependencies (What Needs What)

## Task

Identify all **dependency relationships** between concepts and operations. This defines data flow and execution order.

## Inputs

- `input_1` — The refined instruction
- `input_2` — Extracted concepts
- `input_3` — Extracted operations

---

## The Core Question

For every concept and operation, ask:

> **"What do I need to produce this?"**

This recursion builds the dependency graph:
1. What's the final output?
2. What operation produces it?
3. What does that operation need?
4. Repeat for each input...

---

## Dependency Types

| Type | Meaning | Example |
|------|---------|---------|
| **produces** | Operation creates concept | "extract sentiment" → produces → "sentiment score" |
| **needs** | Operation requires concept | "extract sentiment" ← needs ← "customer review" |
| **sequence** | One after another | "generate report" ← after ← "iteration completes" |
| **aggregates** | Collection built from items | "positive reviews" ← collects ← "review" (per iteration) |
| **conditions** | Boolean controls execution | "add to list" ← gated by ← "is positive" |
| **selects_from** | Selection chooses between options | "result" ← selects_from ← ["option A", "option B"] |
| **discriminates** | Value determines selection choice | "select" ← discriminated_by ← "concept type" |

---

## Selection Dependencies (Important!)

When you have a **selection pattern** ("if A do X, if B do Y, if C do Z"), the dependencies are:

1. **Discriminator**: What value determines the choice (e.g., "concept type")
2. **Condition checks**: Each option needs a condition check (e.g., "is type A")
3. **Gated operations**: Each option's operation is gated by its condition
4. **Selection operator**: Picks the first valid result

**Execution Order Matters**:
1. First: Judge/produce the discriminator value
2. Second: Check each condition against the discriminator
3. Third: Execute the matching gated operation
4. Fourth: Selection operator picks the result

This order must be reflected in the dependencies!

---

## Indicator Phrases

**Temporal order**:
- "after X", "then", "once X is complete" → sequence dependency
- "first X, then Y" → X before Y

**Data flow**:
- "using X", "from X", "based on X" → X is input
- "produces Y", "results in Y" → Y is output

**Aggregation**:
- "collect all", "add to", "gather" → items → collection

---

## Output Format

```json
{
  "thinking": "Your dependency analysis",
  "result": {
    "dependencies": [
      {
        "from": "source concept or operation",
        "to": "target concept or operation",
        "type": "produces | needs | sequence | aggregates | conditions",
        "description": "Why this dependency exists"
      }
    ],
    "data_flow": [
      {
        "operation": "operation name",
        "inputs": ["input concept names"],
        "output": "output concept name"
      }
    ],
    "summary": {
      "root_output": "final output concept",
      "ground_inputs": ["concepts with no producer"],
      "execution_order": ["operation1", "operation2", "..."]
    }
  }
}
```

**Important**: Put all data in the `result` field. The `thinking` field is for your reasoning only.

---

## Example

**Instruction**: "For each review, extract sentiment. If positive, add to positive reviews. Generate report from positive reviews."

**Concepts**: customer reviews, customer review, sentiment score, is positive, positive reviews, summary report

**Operations**: iterate, extract sentiment, check if positive, add to list, generate report

```json
{
  "thinking": "Report needs positive reviews. Positive reviews built by conditional append. Append needs review and condition. Condition needs sentiment. Sentiment needs review. Review comes from iteration over reviews.",
  "result": {
    "dependencies": [
      {"from": "generate report", "to": "summary report", "type": "produces", "description": "Report operation produces output"},
      {"from": "positive reviews", "to": "generate report", "type": "needs", "description": "Report needs collected reviews"},
      {"from": "add to list", "to": "positive reviews", "type": "aggregates", "description": "Collection built by appends"},
      {"from": "is positive", "to": "add to list", "type": "conditions", "description": "Append only if positive"},
      {"from": "check if positive", "to": "is positive", "type": "produces", "description": "Check produces condition"},
      {"from": "sentiment score", "to": "check if positive", "type": "needs", "description": "Check needs score"},
      {"from": "extract sentiment", "to": "sentiment score", "type": "produces", "description": "Extraction produces score"},
      {"from": "customer review", "to": "extract sentiment", "type": "needs", "description": "Extract from current review"},
      {"from": "iterate", "to": "customer review", "type": "produces", "description": "Iteration provides current item"},
      {"from": "customer reviews", "to": "iterate", "type": "needs", "description": "Iterate over collection"}
    ],
    "data_flow": [
      {"operation": "iterate", "inputs": ["customer reviews"], "output": "customer review"},
      {"operation": "extract sentiment", "inputs": ["customer review"], "output": "sentiment score"},
      {"operation": "check if positive", "inputs": ["sentiment score"], "output": "is positive"},
      {"operation": "add to list", "inputs": ["customer review", "is positive"], "output": "positive reviews"},
      {"operation": "generate report", "inputs": ["positive reviews"], "output": "summary report"}
    ],
    "summary": {
      "root_output": "summary report",
      "ground_inputs": ["customer reviews"],
      "execution_order": ["iterate", "extract sentiment", "check if positive", "add to list", "generate report"]
    }
  }
}
```

---

## Common Mistakes

1. **Wrong direction**: Dependencies flow from inputs TO outputs, not reverse
2. **Missing conditions**: Conditional operations depend on their condition
3. **Missing aggregation**: Collections depend on their item source
4. **Missing selection structure**: For "if A do X, if B do Y", need:
   - Discriminator that determines choice
   - Condition checks for each option
   - Gated operations for each option
   - Selection operator to pick result
5. **Wrong order in selection**: Conditions must be evaluated BEFORE the gated operations that use them

---

## Now Extract

### Instruction
$input_1

### Concepts
$input_2

### Operations
$input_3
