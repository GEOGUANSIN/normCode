# Formalize Judgement Concept

Apply judgement `::<{}>` formalization syntax to this function concept.

## Input

The concept line to formalize:
```json
$input_1
```

## Judgement Syntax Rules

Judgements represent evaluations that return boolean using `::<{}>` syntax.

### Format
```
<= ::(description)<{quantifier condition}>
    | %{norm_input}: paradigm-name
    | %{v_input_norm}: prompt_location|script_location
    | %{v_input_provision}: provisions/path/to/resource
    | %{h_input_norm}: Literal
    | %{body_faculty}: llm|python_interpreter
```

### Quantifier Conditions

Add after the description in `<{}>`:
- `<{ALL True}>` - All elements must be true
- `<{ANY True}>` - At least one element true
- `<{ALL False}>` - All elements must be false

### Required Annotations

Same as imperative, but paradigm should output boolean:
- `v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Boolean` for LLM
- `v_ScriptLocation-h_Literal-c_Execute-o_Boolean` for Python

### Example
```
<= ::(check if concept type equals object)<{ALL True}>
    | %{norm_input}: v_ScriptLocation-h_Literal-c_Execute-o_Boolean
    | %{v_input_norm}: script_location
    | %{v_input_provision}: provisions/scripts/check_type.py
    | %{v_function_name}: check_type
    | %{h_input_norm}: Literal
    | %{body_faculty}: python_interpreter
```

### Key Difference from Imperative
- Uses `o_Boolean` paradigms (not `o_Literal`)
- Often includes quantifier condition `<{ALL True}>`
- Output is always a proposition (truth value)

## Output

Return JSON with thinking and result:

```json
{
  "thinking": "Explain what paradigm and annotations were chosen and why",
  "result": "The complete formalized line with all paradigm annotations"
}
```
