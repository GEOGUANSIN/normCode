# Formalize Relation Concept

Apply relation `[name]` formalization syntax to this concept line.

## Input

The concept line to formalize:
```json
$input_1
```

## Relation Syntax Rules

Relations represent collections/lists using `[name]` syntax.

### Format
```
<- [concept name]
    | %{ref_axes}: [item_axis]
    | %{ref_shape}: (n_items,)
    | %{ref_element}: element_type
```

### Annotations to Add

1. **`%{ref_axes}`** - The iteration axis
   - `[item]`, `[line]`, `[element]`, or domain-specific axis
   - Should match what the collection contains

2. **`%{ref_shape}`** - Shape with variable dimension
   - `(n_item,)` where n_item is the count
   - Use descriptive prefixes like `n_`, `num_`

3. **`%{ref_element}`** - What each element contains
   - `str` for string lists
   - `dict(field1: type, field2: type)` for structured items
   - Primitive types for simple lists

### Example
```
<- [parsed lines]
    | %{ref_axes}: [line]
    | %{ref_shape}: (n_line,)
    | %{ref_element}: dict(flow_index: str, content: str, depth: int)
```

## Output

Return the formalized line(s) as a JSON object:

```json
{
  "formalized_line": "The complete formalized line with proper indentation and annotations",
  "annotations_added": ["list of annotation keys added"]
}
```

