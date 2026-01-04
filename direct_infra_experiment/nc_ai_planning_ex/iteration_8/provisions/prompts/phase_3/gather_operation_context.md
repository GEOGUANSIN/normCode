# Gather Operation Context

## Task

For a specific operation, gather all relevant context from the extraction data that will help classify the operation's pattern type.

## Inputs

You will receive:
- `$input_1` — The operation to analyze (current operation)
- `$input_2` — Full extraction results (extraction data) containing concepts, operations, dependencies, patterns

## Context to Gather

1. **Related concepts**: What concepts does this operation interact with?
2. **Input/output role**: What are its inputs and outputs?
3. **Dependency position**: Where is it in the dependency chain?
4. **Control flow context**: Is it inside a loop? Conditional?
5. **Similar operations**: Are there related operations?

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your context gathering process",
  "context": {
    "operation": "the operation being analyzed",
    "input_concepts": ["list of concepts this operation takes as input"],
    "output_concept": "concept this operation produces",
    "is_inside_loop": true/false,
    "loop_context": "if inside loop, what loop",
    "is_conditional": true/false,
    "condition_context": "if conditional, what condition",
    "upstream_operations": ["operations that must complete before this"],
    "downstream_operations": ["operations that depend on this"],
    "similar_operations": ["other operations with similar pattern"],
    "body_faculty_hint": "llm" | "file_system" | "python_interpreter"
  }
}
```

## Example

For operation `extract sentiment` with extraction data showing it's inside a `for each review` loop:

```json
{
  "context": {
    "operation": "extract sentiment",
    "input_concepts": ["{review}"],
    "output_concept": "{sentiment}",
    "is_inside_loop": true,
    "loop_context": "for each review in [reviews]",
    "is_conditional": false,
    "condition_context": null,
    "upstream_operations": [],
    "downstream_operations": ["generate report"],
    "similar_operations": ["extract key themes"],
    "body_faculty_hint": "llm"
  }
}
```

## Operation to Analyze

### Current Operation
$input_1

### Extraction Data
$input_2

