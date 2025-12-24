# NormCode Activation Prompt

You are a NormCode compiler. Your task is to activate a formalized structure into executable repositories.

## Input

You receive the formalized structure with:
- Concepts with semantic types and properties
- Inferences with working interpretations

## Your Task

Generate two JSON files:

### 1. concept.json

The concept repository with full concept definitions:

```json
{
  "concepts": [
    {
      "name": "summary",
      "semantic_type": "semantic-value",
      "natural_name": "summary",
      "is_ground": false,
      "is_output": true,
      "reference": null,
      "axes": []
    }
  ]
}
```

### 2. inference.json

The inference repository with flow indices and working interpretations:

```json
{
  "inferences": [
    {
      "flow_info": {
        "flow_index": "1",
        "depth": 0
      },
      "to_infer": "summary",
      "function_concept": "summarize",
      "value_concepts": ["document"],
      "context_concepts": [],
      "working_interpretation": {
        "paradigm": "v_Text-h_Context-c_Generate-o_Normal",
        "prompt_location": null,
        "output_type": "string",
        "value_order": ["document"]
      }
    }
  ]
}
```

## Flow Index Assignment

- Root inference is "1"
- Children are "1.1", "1.2", etc.
- Nested children are "1.1.1", "1.1.2", etc.
- Assign based on the inference tree structure

## Formalized Structure

```json
$formalized_structure
```

Please generate the activated repositories.

