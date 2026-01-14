# Formalize Imperative Concept

Apply imperative `::()` formalization syntax to this function concept.

## Input

The concept line to formalize:
```json
$input_1
```

## Imperative Syntax Rules

Imperatives represent actions/transformations using `::()` syntax.

### Format
```
<= ::(action description)
    | %{norm_input}: paradigm-name
    | %{v_input_norm}: prompt_location|script_location
    | %{v_input_provision}: provisions/path/to/resource
    | %{h_input_norm}: Literal|LiteralPath
    | %{body_faculty}: llm|file_system|python_interpreter
```

### Required Annotations

1. **`%{norm_input}`** - The paradigm to use
   - `v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal` for LLM
   - `v_ScriptLocation-h_Literal-c_Execute-o_Literal` for Python
   - `h_LiteralPath-c_ReadFile-o_Literal` for file read

2. **`%{v_input_norm}`** - Vertical input type (if paradigm has v_)
   - `prompt_location` for LLM prompts
   - `script_location` for Python scripts

3. **`%{v_input_provision}`** - Path to the resource
   - `provisions/prompts/...` for prompts
   - `provisions/scripts/...` for scripts

4. **`%{h_input_norm}`** - Horizontal input handling
   - `Literal` - MVP perceives perceptual signs → passes content
   - `LiteralPath` - MVP passes path as-is → paradigm reads file

5. **`%{body_faculty}`** - Which tool executes this
   - `llm` for AI generation
   - `python_interpreter` for scripts
   - `file_system` for file I/O

### Example
```
<= ::(parse .ncds file into JSON list of lines)
    | %{norm_input}: v_ScriptLocation-h_Literal-c_Execute-o_Literal
    | %{v_input_norm}: script_location
    | %{v_input_provision}: provisions/scripts/ncds_parser.py
    | %{v_function_name}: parse_ncds
    | %{h_input_norm}: Literal
    | %{body_faculty}: python_interpreter
```

## Output

Return JSON with thinking and result:

```json
{
  "thinking": "Explain what paradigm and annotations were chosen and why",
  "result": "The complete formalized line with all paradigm annotations"
}
```
