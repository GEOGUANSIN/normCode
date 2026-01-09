# Identify Goal (Final Output Concept)

## Task

Identify the **final output concept** (goal) from the extraction data. This will be the root of the dependency tree.

## Input

- `input_1` — Full extraction results (extraction data) containing concepts, operations, dependencies, patterns

---

## The Core Derivation Question

From the derivation process, the fundamental question is:

> **"What do I need to produce this?"**

But first, we must answer: **"What is the final output?"**

The goal concept is what the entire plan exists to produce. Everything else in the plan exists only to support producing this goal.

---

## How to Identify the Goal

The goal concept has these characteristics:

### 1. Explicitly Marked as Output
In extraction data, concepts have roles:
- `input` — Ground data provided at start
- `intermediate` — Produced and consumed within the plan
- `output` — The final result (this is the goal)

### 2. Has No Dependents
The goal is a **sink** in the dependency graph:
- Other operations produce it
- Nothing else consumes it
- It's the end of the data flow chain

### 3. Is Produced Last
Following the dependency chain:
- Start from any input
- Trace forward through operations
- The concept you eventually reach that has no outgoing edges is the goal

### 4. Matches the Instruction's Stated Goal
The user's original instruction usually describes what they want:
- "Generate a report" → goal is the report
- "Classify the documents" → goal is the classifications
- "Answer the question" → goal is the answer

---

## The Dependency Tree Structure

From `derivation_v2.md`, every derivation produces a tree:

| Node Type | Symbol | Question It Answers |
|-----------|--------|---------------------|
| **Value** | `<-` | "What data exists here?" |
| **Function** | `<=` | "What operation produces it?" |
| **Context** | `<*` | "What controls or scopes this?" |

The goal becomes the **root** of this tree:

```
goal (root)
└── operation that produces it
    └── input 1
    └── input 2
        └── operation that produces input 2
            └── ...
```

---

## Selection Criteria When Multiple Candidates Exist

If multiple concepts seem like potential goals, prefer:

| Priority | Criterion | Reasoning |
|----------|-----------|-----------|
| 1 | Explicitly marked `role: output` | Direct annotation |
| 2 | No downstream dependencies | Nothing consumes it |
| 3 | Aggregates/summarizes others | Final synthesis step |
| 4 | Matches instruction goal phrase | User intent alignment |
| 5 | Object type `{}` over collection `[]` | Final outputs are often singular |

---

## Common Goal Indicators

| Phrase in Instruction | Likely Goal Concept |
|----------------------|---------------------|
| "Generate a report" | report (object) |
| "Produce a summary" | summary (object) |
| "Classify the items" | classifications (collection) |
| "Answer the question" | answer (object) |
| "Extract all X" | all X (collection) |
| "Determine if X" | X determination (condition) |
| "Make a decision" | decision (object) |

---

## Output Format

```json
{
  "thinking": "Your analysis of the extraction data to find the goal",
  "result": {
    "concept_name": "the goal concept name",
    "concept_type": "object | collection | condition",
    "description": "what this goal represents",
    "confidence": 0.0-1.0,
    "alternatives": ["other possible goal concepts, if any"],
    "reasoning": "why this is the goal"
  }
}
```

**Important**: Put the goal in the `result` field. The `thinking` field is for your reasoning only.

---

## Example

**Extraction Data Summary**:
- Concepts:
  - `reviews` (collection, input)
  - `review` (object, loop_var)
  - `sentiment` (object, intermediate)
  - `all sentiments` (collection, intermediate)
  - `summary report` (object, output)
- Operations: iterate over reviews, extract sentiment, summarize all sentiments
- Dependencies: 
  - extract sentiment needs review
  - summarize needs all sentiments
  - summary report has no consumers

**Analysis**:

```json
{
  "thinking": "Looking at the concepts: 'reviews' is input (ground), 'review' is loop variable, 'sentiment' and 'all sentiments' are intermediates. Only 'summary report' is marked as output. Checking dependencies: nothing consumes 'summary report' - it's the sink. Instruction was 'generate summary from reviews' - matches 'summary report'. Confidence high.",
  "result": {
    "concept_name": "summary report",
    "concept_type": "object",
    "description": "A synthesized report summarizing all sentiment findings from the reviews",
    "confidence": 0.95,
    "alternatives": [],
    "reasoning": "Explicitly marked as output, no downstream dependencies, matches instruction goal, is the final aggregation of all intermediate results"
  }
}
```

---

## Common Mistakes

| Mistake | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| Choosing an input as goal | Inputs are consumed, not produced | Goal is always produced by the plan |
| Choosing intermediate | Intermediates have downstream ops | Goal has no consumers |
| Choosing loop variable | Loop vars are scoped to iteration | Goal is at top level |
| Multiple goals | NormCode plans have ONE output | Find the single final output |

---

## Extraction Data to Analyze

$input_1
