# Extract Dependencies (What Needs What)

## Task

Identify all **dependency relationships** between concepts and operations. These define the data flow and execution order in the NormCode plan.

## Inputs

You will receive:
- `{refined instruction content}`: The refined instruction
- `{extracted concepts}`: List of extracted value concepts
- `[extracted operations]`: List of extracted operations

## What to Extract

For each operation, determine:
1. **Input concepts**: What data does this operation need?
2. **Output concept**: What data does this operation produce?
3. **Prerequisites**: What other operations must complete first?

## Dependency Types

| Type | Example | Meaning |
|------|---------|---------|
| **Data flow** | `{summary}` ← `summarize` ← `{document}` | Operation uses input to produce output |
| **Sequence** | `validate` → `process` | One operation must complete before another |
| **Aggregation** | `{all summaries}` ← `collect` ← `[{summary}]` | Collection of results from loop |

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your dependency analysis",
  "dependencies": [
    {
      "target": "concept or operation that depends",
      "source": "concept or operation depended upon",
      "relationship": "data_input" | "produces" | "sequence" | "aggregates",
      "description": "Why this dependency exists"
    }
  ],
  "data_flow": [
    {
      "operation": "operation name",
      "inputs": ["list of input concepts"],
      "output": "output concept"
    }
  ],
  "execution_order_hints": ["operation1 before operation2", ...]
}
```

## Example

Concepts: `[reviews]`, `{review}`, `{sentiment}`, `{report}`
Operations: `for each review`, `extract sentiment`, `generate report`

Dependencies:
```json
{
  "dependencies": [
    {"target": "{sentiment}", "source": "extract sentiment", "relationship": "produces"},
    {"target": "extract sentiment", "source": "{review}", "relationship": "data_input"},
    {"target": "{report}", "source": "generate report", "relationship": "produces"},
    {"target": "generate report", "source": "[{sentiment}]", "relationship": "data_input"}
  ]
}
```

## Data to Analyze

### Instruction
{{refined instruction content}}

### Concepts
{{extracted concepts}}

### Operations
{{extracted operations}}

