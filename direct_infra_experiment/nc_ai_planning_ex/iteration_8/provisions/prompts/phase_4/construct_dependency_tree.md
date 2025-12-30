# Construct Dependency Tree

## Task

Build a **dependency tree** structure from the goal concept, classified operations, and dependency relationships. This tree will be serialized to the final .ncds format.

## Inputs

You will receive:
- `{final output concept}`: The goal/root concept
- `{classified operations}`: Operations with their pattern classifications
- `[all dependencies]`: Dependency relationships between concepts/operations

## Tree Structure

Each node in the tree has:
- **concept**: The concept at this node
- **operation**: The operation that produces this concept (if any)
- **pattern**: The NormCode pattern type
- **children**: Concepts/operations this node depends on
- **context**: Loop iteration variable (if inside loop)
- **condition**: Condition concept (if conditional)

## Building the Tree

1. **Start from goal**: The root is the final output concept
2. **Find producer**: What operation produces this concept?
3. **Find inputs**: What does that operation need?
4. **Recurse**: For each input, repeat steps 2-3
5. **Handle patterns**:
   - **Loops**: Add context marker for iteration variable
   - **Conditionals**: Add condition concept reference
   - **Grouping**: Children are the items being grouped
   - **Selection**: Children are the options to select from

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your tree construction process",
  "tree": {
    "root": "goal concept name",
    "nodes": {
      "concept_name": {
        "operation": "operation that produces this concept",
        "pattern": "linear" | "multi-input" | "iteration" | etc.,
        "children": ["list of child concept names"],
        "context": "iteration variable if in loop, or null",
        "condition": "condition concept if conditional, or null",
        "is_ground": true/false
      }
    }
  },
  "ground_concepts": ["list of concepts with no producer - inputs"],
  "depth": <maximum tree depth>
}
```

## Example

For a review summarization task:

```json
{
  "tree": {
    "root": "{summary report}",
    "nodes": {
      "{summary report}": {
        "operation": "generate summary report",
        "pattern": "multi-input",
        "children": ["[all sentiments]", "[all themes]"],
        "context": null,
        "condition": null,
        "is_ground": false
      },
      "[all sentiments]": {
        "operation": "for each review extract sentiment",
        "pattern": "iteration",
        "children": ["{sentiment}", "[reviews]"],
        "context": "{review}",
        "condition": null,
        "is_ground": false
      },
      "{sentiment}": {
        "operation": "extract sentiment",
        "pattern": "linear",
        "children": ["{review}"],
        "context": null,
        "condition": null,
        "is_ground": false
      },
      "[reviews]": {
        "operation": null,
        "pattern": null,
        "children": [],
        "context": null,
        "condition": null,
        "is_ground": true
      }
    }
  },
  "ground_concepts": ["[reviews]"],
  "depth": 4
}
```

## Data to Analyze

### Goal
{{final output concept}}

### Classified Operations
{{classified operations}}

### Dependencies
{{all dependencies}}

