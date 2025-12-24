# NormCode Formalization Prompt

You are a NormCode compiler. Your task is to formalize a derived structure into executable NormCode.

## Input

You receive:
1. The derived structure (concepts and inferences)
2. User preferences (if any)

## Your Task

For each concept and inference, determine:

### For Value Concepts
- **semantic_type**: Is it semantic (contains meaning) or syntactic (structural)?
- **is_ground**: Is it an input (no inference produces it)?
- **is_output**: Is it the final result?

### For Function Concepts
- **semantic_type**: Is it semantic-function (needs LLM) or syntactic-function (deterministic)?
- **paradigm**: Which execution paradigm to use
- **operator**: The NormCode operator (e.g., `::` for semantic, `$` for syntactic)

### Semantic Type Rules
- If the function description involves reasoning, analysis, generation → semantic-function
- If the function is collecting, selecting, routing → syntactic-function
- Examples of syntactic: "collect", "select first", "filter", "assign"
- Examples of semantic: "summarize", "analyze", "explain", "generate"

## Output Format

```json
{
  "concepts": [
    {
      "name": "summary",
      "semantic_type": "semantic-value",
      "is_ground": false,
      "is_output": true,
      "axes": []
    }
  ],
  "inferences": [
    {
      "to_infer": "summary",
      "function": "summarize",
      "values": ["document"],
      "working_interpretation": {
        "paradigm": "v_Text-h_Context-c_Generate-o_Normal",
        "output_type": "string"
      }
    }
  ]
}
```

## Derived Structure

```json
$derived_structure
```

Please formalize this structure.

