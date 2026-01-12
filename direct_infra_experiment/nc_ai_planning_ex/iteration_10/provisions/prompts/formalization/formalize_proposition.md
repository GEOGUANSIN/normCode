# Formalize Proposition Concept

Apply proposition `<name>` formalization syntax to this concept line.

## Input

The concept line to formalize:
```json
$input_1
```

## Proposition Syntax Rules

Propositions represent truth values/conditions using `<name>` syntax.

### Format
```
<- <concept name>
    | %{ref_axes}: [_none_axis]
    | %{ref_shape}: (1,)
    | %{ref_element}: %{truth_value}
```

### Key Points

1. **Always use `%{truth_value}`** as the element type
   - This is the special marker for boolean/truth values

2. **Shape is typically `(1,)`** for single boolean
   - Use `(n,)` for arrays of booleans

3. **Axes are typically `[_none_axis]`** for scalars

### Example
```
<- <is object type>
    | %{ref_axes}: [_none_axis]
    | %{ref_shape}: (1,)
    | %{ref_element}: %{truth_value}
```

### Used For
- Conditional checks: `<is valid>`, `<has error>`
- Type checks: `<is object type>`, `<is imperative type>`
- State flags: `<phase complete>`, `<file exists>`

## Output

Return the formalized line(s) as a JSON object:

```json
{
  "formalized_line": "The complete formalized line with proper indentation and annotations",
  "annotations_added": ["list of annotation keys added"]
}
```

