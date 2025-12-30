# Extract Control Patterns (Loops and Conditions)

## Task

Identify all **control flow patterns** in the instruction. These become syntactic operators (`*`, `@`) in the NormCode plan.

## Input

You will receive:
- `{refined instruction content}`: The refined instruction

## Control Pattern Types

### Iteration Patterns (`*` Looping)

| Trigger Phrase | Pattern | Example |
|----------------|---------|---------|
| "for each X" | Loop over collection | `for each document in [documents]` |
| "for every X" | Loop over collection | `for every item` |
| "process all X" | Loop over collection | `process all files` |
| "repeat until" | Loop with condition | `repeat until done` |

### Conditional Patterns (`@` Timing)

| Trigger Phrase | Pattern | Example |
|----------------|---------|---------|
| "if X then Y" | Conditional execution | `if valid then process` |
| "when X" | Conditional execution | `when ready execute` |
| "unless X" | Negated conditional | `unless error continue` |
| "only if X" | Gated execution | `only if approved` |
| "after X" | Sequencing | `after validation` |

### Selection Patterns (`$` Assigning)

| Trigger Phrase | Pattern | Example |
|----------------|---------|---------|
| "choose first valid" | Specification | `choose first valid result` |
| "select X or Y" | Selection | `select cached or fresh` |
| "use X if available" | Fallback | `use cached if available` |

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your pattern analysis",
  "patterns": [
    {
      "type": "loop" | "conditional" | "selection" | "sequence",
      "subtype": "for_each" | "if_then" | "if_not" | "after" | "first_valid",
      "trigger_phrase": "The phrase that indicates this pattern",
      "elements": {
        "collection": "for loops - what is iterated over",
        "current_item": "for loops - the current element name",
        "condition": "for conditionals - what is being checked",
        "true_branch": "for conditionals - what happens if true",
        "false_branch": "for conditionals - what happens if false (optional)"
      },
      "normcode_operator": "*." | "@:'" | "@:!" | "@." | "$."
    }
  ],
  "pattern_count": <number of patterns found>
}
```

## Example

Instruction: "For each file, if the file is valid then process it, otherwise log an error"

Patterns:
```json
{
  "patterns": [
    {
      "type": "loop",
      "subtype": "for_each",
      "trigger_phrase": "For each file",
      "elements": {"collection": "[files]", "current_item": "{file}"},
      "normcode_operator": "*."
    },
    {
      "type": "conditional",
      "subtype": "if_then",
      "trigger_phrase": "if the file is valid",
      "elements": {"condition": "<file is valid>", "true_branch": "process it"},
      "normcode_operator": "@:'"
    },
    {
      "type": "conditional", 
      "subtype": "if_not",
      "trigger_phrase": "otherwise",
      "elements": {"condition": "<file is valid>", "false_branch": "log an error"},
      "normcode_operator": "@:!"
    }
  ]
}
```

## Instruction to Analyze

{{refined instruction content}}

