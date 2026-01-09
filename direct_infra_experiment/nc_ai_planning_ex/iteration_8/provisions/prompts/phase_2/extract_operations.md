# Extract Operations (Verbs and Actions)

## Task

Identify all **operations** (actions, transformations, evaluations) from the refined instruction. These are the "verbs" that transform or evaluate data.

## Input

- `input_1` — The refined instruction

---

## What Are Operations?

Operations are the **verbs** of your plan—they transform data or evaluate conditions.

### Two Main Types

| Type | What It Does | Output | How to Recognize |
|------|--------------|--------|------------------|
| **Imperative** | Executes an action | New data | "calculate", "extract", "generate", "read", "write" |
| **Judgement** | Evaluates a condition | True/False | "check if", "is X?", "determine whether", "validate" |

### Operation Categories

| Category | Examples | Execution |
|----------|----------|-----------|
| **Generation** | Generate text, create response | LLM |
| **Analysis** | Analyze sentiment, understand intent | LLM |
| **Extraction** | Extract entities, parse meaning | LLM |
| **Evaluation** | Judge quality, check validity | LLM or Script |
| **File I/O** | Read file, write to file | Script |
| **Computation** | Calculate sum, divide | Script |
| **Iteration** | For each X, process all | Control flow |
| **Selection** | Select first valid, choose based on type | Control flow |
| **Aggregation** | Collect, bundle, combine | Control flow |
| **Return** | Return result for this item (in loops) | Control flow |

### Special Operations

**Loop Return Operations**: Inside a loop, there's always an implicit or explicit "return" operation that specifies what gets collected:
- "return the processed item" → what gets aggregated
- Often implied by "for each X, do Y" → Y is returned

**Selection Operations**: When choosing between multiple options:
- "select first valid option" → the selection operator
- "apply appropriate formalization" → implies selection based on some criterion

---

## LLM vs Script

| Use LLM when... | Use Script when... |
|-----------------|-------------------|
| Understanding/reasoning needed | Exact computation required |
| Natural language generation | Structured data parsing |
| Subjective judgment | Numeric comparison |
| "Analyze", "Understand", "Generate" | "Calculate", "Parse", "Check if equals" |

---

## What to Extract

**Include**:
- Action verbs (calculate, extract, generate, read, write)
- Transformations (convert, parse, format, clean)
- Evaluations (check, validate, determine if)
- I/O operations (read, write, load, save)
- Aggregations (combine, collect, merge, bundle)
- Loop operations (for each, process all)

**Exclude**:
- Data objects (nouns are concepts, not operations)
- Static descriptions

---

## Output Format

```json
{
  "thinking": "Your analysis identifying each operation",
  "result": {
    "operations": [
      {
        "name": "operation description",
        "type": "imperative | judgement",
        "category": "generation | analysis | extraction | evaluation | file_io | computation | iteration | aggregation",
        "execution": "llm | script",
        "source_phrase": "The phrase from the instruction",
        "inputs_hint": ["likely input concepts"],
        "output_hint": "likely output concept"
      }
    ],
    "summary": {
      "imperative_count": 0,
      "judgement_count": 0,
      "llm_operations": 0,
      "script_operations": 0
    }
  }
}
```

**Important**: Put all data in the `result` field. The `thinking` field is for your reasoning only.

---

## Example

**Instruction**: "For each customer review, extract sentiment. If positive (score > 0.7), add to positive reviews. Generate a summary report."

```json
{
  "thinking": "'For each' is iteration. 'extract sentiment' is LLM extraction. 'If positive (score > 0.7)' is a comparison judgement. 'add to' is aggregation. 'Generate report' is LLM generation.",
  "result": {
    "operations": [
      {"name": "iterate over customer reviews", "type": "imperative", "category": "iteration", "execution": "script", "source_phrase": "For each customer review", "inputs_hint": ["customer reviews"], "output_hint": "customer review"},
      {"name": "extract sentiment score", "type": "imperative", "category": "extraction", "execution": "llm", "source_phrase": "extract sentiment", "inputs_hint": ["customer review"], "output_hint": "sentiment score"},
      {"name": "check if score is positive", "type": "judgement", "category": "evaluation", "execution": "script", "source_phrase": "If positive (score > 0.7)", "inputs_hint": ["sentiment score"], "output_hint": "is positive"},
      {"name": "add review to positive reviews", "type": "imperative", "category": "aggregation", "execution": "script", "source_phrase": "add to positive reviews", "inputs_hint": ["customer review", "is positive"], "output_hint": "positive reviews"},
      {"name": "generate summary report", "type": "imperative", "category": "generation", "execution": "llm", "source_phrase": "Generate a summary report", "inputs_hint": ["positive reviews"], "output_hint": "summary report"}
    ],
    "summary": {
      "imperative_count": 4,
      "judgement_count": 1,
      "llm_operations": 2,
      "script_operations": 3
    }
  }
}
```

---

## Common Mistakes

1. **Missing judgement type**: "check if X" produces boolean → it's a judgement
2. **Wrong execution**: "score > 0.7" is exact comparison → script, not LLM
3. **Missing iteration**: "for each" is an operation, not just context

---

## Now Extract

$input_1
