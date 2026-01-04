# Extract Operations (Verbs and Actions)

## Task

Identify all **functional concepts** (operations, actions, transformations) from the refined instruction. These will become `<=` (functional concept) markers in the NormCode plan.

## Input

You will receive:
- `$input_1` — The refined, concrete instruction (refined instruction content)

## What to Extract

**Include**:
- Action verbs (extract, generate, analyze, calculate, etc.)
- Transformations (convert, parse, format, etc.)
- I/O operations (read, write, load, save, etc.)
- Evaluations (check, validate, determine if, etc.)
- Aggregations (combine, collect, merge, etc.)

**Exclude**:
- Static descriptions (not actions)
- Data objects (these are concepts, not operations)

## Operation Type Hints

| Pattern | Type | Example |
|---------|------|---------|
| Action verb | Imperative | `extract entities`, `generate summary` |
| "check if", "determine if", "is X?" | Judgement | `check if valid`, `is complete?` |
| "for each X do Y" | Looping | `for each document summarize` |
| "if X then Y" | Conditional | `if invalid then retry` |
| "collect", "bundle", "group" | Grouping | `collect all results` |
| "select", "pick", "choose first" | Selection | `select first valid` |

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your analysis of the instruction",
  "operations": [
    {
      "name": "operation description",
      "type": "imperative" | "judgement" | "looping" | "conditional" | "grouping" | "selection",
      "description": "What this operation does",
      "likely_body_faculty": "llm" | "file_system" | "python_interpreter",
      "source_phrase": "The phrase in the instruction this came from"
    }
  ],
  "operation_count": <number of operations found>
}
```

## Example

Instruction: "For each customer review, extract sentiment and key themes, then generate a summary report"

Operations:
- `for each customer review` (looping)
- `extract sentiment` (imperative, llm)
- `extract key themes` (imperative, llm)  
- `generate summary report` (imperative, llm)

## Instruction to Analyze

$input_1

