# Extract Concepts (Nouns and Data Entities)

## Task

Identify all **data entities** (nouns, values, states) from the refined instruction. These are the "things" that operations will produce, consume, or evaluate.

## Input

- `input_1` — The refined instruction

---

## What Are Concepts?

Concepts are the **nouns** of your plan—the data being manipulated, observed, or produced.

### Three Types of Concepts

| Type | What It Is | How to Recognize |
|------|------------|------------------|
| **Object** | A singular entity or value | "the document", "a file", "the result", "user input" |
| **Collection** | A group of items | "the files", "all numbers", "list of X", "each item" |
| **Condition** | A true/false state | "is valid", "has errors", "should continue", "file exists" |

### Examples

| Natural Language | Type | Concept Name |
|------------------|------|--------------|
| "Calculate the **sum** of the digits" | object | sum |
| "For each **document** in the **documents**" | object + collection | document, documents |
| "If the **file is valid**" | condition | file is valid |
| "The **list of summaries**" | collection | summaries |

---

## Concept Roles

| Role | Description | Example |
|------|-------------|---------|
| **input** | External data provided at start | "the raw file", "user query" |
| **output** | Final result to produce | "the report", "summary" |
| **intermediate** | Computed along the way | "extracted entities", "processed data" |
| **condition** | Boolean for control flow | "is valid", "should continue" |
| **loop_variable** | Current item in iteration | "current file" (from "for each file") |

---

## What to Extract

**Include**:
- Data objects mentioned (document, file, report, message, score)
- Input data (user query, raw data, configuration)
- Output data (summary, result, response)
- Intermediate results (extracted entities, processed content)
- Collections (list of X, all Y, the items)
- Conditions (is valid, has errors, should continue)
- Loop variables (current item when iterating)

**Exclude**:
- Actions/verbs (these are operations)
- The plan's meta-description
- Generic system terms

---

## Extraction Steps

1. **Find the output** - What is the final result?
2. **Find the inputs** - What data exists at the start?
3. **Find intermediates** - What gets computed along the way?
4. **Find conditions** - What boolean states affect flow?
5. **Find loop variables** - If there's "for each X", what is X?

---

## Output Format

```json
{
  "thinking": "Your analysis identifying each concept",
  "concepts": [
    {
      "name": "concept name in natural language",
      "type": "object" | "collection" | "condition",
      "role": "input" | "output" | "intermediate" | "condition" | "loop_variable",
      "description": "What this concept represents",
      "source_phrase": "The phrase from the instruction"
    }
  ],
  "summary": {
    "output_concept": "name of the final output",
    "input_concepts": ["names of input concepts"],
    "total_count": 0
  }
}
```

---

## Example

**Instruction**: "For each customer review, extract sentiment. If positive (score > 0.7), add to positive reviews. Generate a summary report from positive reviews."

```json
{
  "thinking": "Output is 'summary report'. Input is 'customer reviews' (collection). Loop variable is 'customer review'. Intermediate: 'sentiment score', 'positive reviews'. Condition: 'is positive'.",
  "concepts": [
    {"name": "customer reviews", "type": "collection", "role": "input", "description": "Reviews to process", "source_phrase": "For each customer review"},
    {"name": "customer review", "type": "object", "role": "loop_variable", "description": "Current review in iteration", "source_phrase": "For each customer review"},
    {"name": "sentiment score", "type": "object", "role": "intermediate", "description": "Extracted sentiment value", "source_phrase": "extract sentiment"},
    {"name": "is positive", "type": "condition", "role": "condition", "description": "Whether score > 0.7", "source_phrase": "If positive (score > 0.7)"},
    {"name": "positive reviews", "type": "collection", "role": "intermediate", "description": "Reviews meeting threshold", "source_phrase": "add to positive reviews"},
    {"name": "summary report", "type": "object", "role": "output", "description": "Final report", "source_phrase": "Generate a summary report"}
  ],
  "summary": {
    "output_concept": "summary report",
    "input_concepts": ["customer reviews"],
    "total_count": 6
  }
}
```

---

## Common Mistakes

1. **Missing loop variable**: "for each file" → extract both "files" (collection) AND "file" (current item)
2. **Wrong type**: "all summaries" is a collection, not an object
3. **Missing conditions**: "if valid" → extract "is valid" as a condition

---

## Now Extract

$input_1
