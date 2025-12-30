# Classify Operation Pattern

## Task

Determine the **NormCode pattern type** for a specific operation based on the operation itself and its gathered context.

## Inputs

You will receive:
- `{current operation}`: The operation to classify
- `{operation context}`: Gathered context about this operation

## Pattern Classification

### Semantic Patterns (require LLM)

| Pattern | Description | NormCode Marker |
|---------|-------------|-----------------|
| **linear** | Simple input → output transformation | `<= ::(operation)` |
| **multi-input** | Multiple inputs → single output | `<= ::(operation)` with multiple `<-` |
| **judgement** | Produces boolean/condition | `<= ::<{check}>` |

### Syntactic Patterns (no LLM)

| Pattern | Description | NormCode Operator |
|---------|-------------|-------------------|
| **iteration** | For each item in collection | `<= *. %>({base}) ...` |
| **conditional** | If condition then execute | `<= @:'(<condition>)` |
| **grouping** | Collect items together | `<= &[{}] ...` or `<= &[#] ...` |
| **selection** | Pick first valid | `<= $. %>({source})` |

## Classification Criteria

**Linear**:
- Single input → single output
- Direct transformation
- No control flow

**Multi-input**:
- Multiple inputs
- Synthesis/combination
- No control flow

**Iteration**:
- "for each", "for every"
- Collection as input
- Per-item processing

**Conditional**:
- "if", "when", "unless"
- Boolean gate
- Branch execution

**Grouping**:
- "collect", "bundle", "gather"
- Multiple items → collection
- Structural combination

**Selection**:
- "choose", "select first", "pick"
- Multiple options → one result
- Priority-based

**Judgement**:
- "check if", "determine if", "is X?"
- Boolean output
- Evaluation/validation

## Output Format

Return a JSON object:

```json
{
  "thinking": "Your classification reasoning",
  "classification": {
    "pattern": "linear" | "multi-input" | "iteration" | "conditional" | "grouping" | "selection" | "judgement",
    "is_semantic": true/false,
    "normcode_marker": "the NormCode operator/marker",
    "body_faculty": "llm" | "file_system" | "python_interpreter" | null,
    "confidence": 0.0-1.0,
    "notes": "Any special considerations"
  }
}
```

## Operation to Classify

### Operation
{{current operation}}

### Context
{{operation context}}

