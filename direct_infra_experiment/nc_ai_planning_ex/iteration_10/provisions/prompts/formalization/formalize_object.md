# Formalize Object Concept

Apply object `{name}` formalization syntax to this concept line.

## Input

The concept line to formalize:
```json
$input_1
```

## Object Syntax Rules

Objects represent singular data entities using `{name}` syntax.

### Format
```
<- {concept name}
    | %{ref_axes}: [axis_names]
    | %{ref_shape}: (dimensions,)
    | %{ref_element}: element_type
```

### Annotations to Add

1. **`%{ref_axes}`** - What dimensions does this data have?
   - `[_none_axis]` for scalar/single values
   - `[item]` for collections
   - `[row, column]` for 2D data

2. **`%{ref_shape}`** - Shape tuple
   - `(1,)` for single value
   - `(n,)` for list
   - `(n, m)` for 2D

3. **`%{ref_element}`** - Element type
   - `str` for strings
   - `dict` for dictionaries
   - `int`, `float`, `bool` for primitives

### Ground Concepts
If this is a ground concept (external input), add:
```
/: Ground: description of this input
```

## Output

Return the formalized line(s) as a JSON object:

```json
{
  "formalized_line": "The complete formalized line with proper indentation and annotations",
  "annotations_added": ["list of annotation keys added"]
}
```

