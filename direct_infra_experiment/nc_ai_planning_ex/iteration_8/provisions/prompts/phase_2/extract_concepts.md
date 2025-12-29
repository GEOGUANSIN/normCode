# Extract Concepts (Nouns and Data Entities)

## Task

Identify all **value concepts** (nouns, data entities) from the refined instruction. These will become `<-` (value concept) markers in the NormCode plan.

## Input

You will receive:
- `{refined instruction content}`: The refined, concrete instruction

## What to Extract

**Include**:
- Explicit data objects (document, file, report, etc.)
- Input data (user query, raw data, etc.)
- Output data (summary, result, analysis, etc.)
- Intermediate results (extracted entities, processed data, etc.)
- Collections (list of X, all Y, etc.)
- State/conditions (is valid, has errors, etc.)

**Exclude**:
- Actions/verbs (these become functional concepts)
- Generic system terms (system, process, execution)
- Meta-concepts about the plan itself

## Concept Type Hints

| Pattern | Type | Example |
|---------|------|---------|
| Singular noun | `{}` Object | `{document}`, `{result}` |
| Plural / "all X" / "list of X" | `[]` Relation | `[files]`, `[summaries]` |
| "is X", "has Y", condition | `<>` Proposition | `<is valid>`, `<has errors>` |

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your analysis of the instruction",
  "concepts": [
    {
      "name": "concept name",
      "type": "{}" | "[]" | "<>",
      "description": "What this concept represents",
      "role": "input" | "output" | "intermediate" | "condition",
      "source_phrase": "The phrase in the instruction this came from"
    }
  ],
  "concept_count": <number of concepts found>
}
```

## Example

Instruction: "For each customer review, extract sentiment and key themes, then generate a summary report"

Concepts:
- `[customer reviews]` (relation, input)
- `{customer review}` (object, intermediate - current item in loop)
- `{sentiment}` (object, intermediate)
- `{key themes}` (object, intermediate)
- `{summary report}` (object, output)

## Instruction to Analyze

{{refined instruction content}}

