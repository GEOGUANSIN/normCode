# Identify Goal (Final Output Concept)

## Task

Identify the **final output concept** (goal) from the extraction data. This will be the root `:<:` (output marker) concept in the NormCode plan.

## Input

You will receive:
- `$input_1` — Full extraction results (extraction data) containing concepts, operations, dependencies, patterns

## How to Identify the Goal

The goal concept is:
1. **Marked as output**: Role is explicitly "output"
2. **Has no dependents**: Nothing else depends on it
3. **Is produced last**: At the end of the dependency chain
4. **Matches the instruction's stated goal**: What the user wants to get

## Selection Criteria

If multiple candidates exist, prefer:
1. Concepts explicitly described as "final result" or "output"
2. Concepts with no downstream dependencies
3. Concepts that summarize/aggregate others
4. Concepts that match the instruction's goal phrase

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your analysis of the extraction data to find the goal",
  "goal": {
    "concept_name": "the goal concept name",
    "concept_type": "{}" | "[]" | "<>",
    "description": "what this goal represents",
    "confidence": 0.0-1.0,
    "alternatives": ["other possible goal concepts, if any"],
    "reasoning": "why this is the goal"
  }
}
```

## Example

Extraction data with concepts:
- `[reviews]` (input)
- `{sentiment}` (intermediate)
- `{summary report}` (output)

Goal: `{summary report}` because:
- Marked as output
- Nothing depends on it
- Aggregates other results
- Matches "generate a summary report" goal

## Extraction Data to Analyze

$input_1

