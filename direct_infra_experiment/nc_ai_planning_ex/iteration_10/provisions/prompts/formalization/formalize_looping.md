# Formalize Looping Operator

Apply looping `*` formalization syntax to this operator concept.

## Input

The concept line to formalize:
```json
$input_1
```

## Looping Syntax Rules

Looping operators iterate over collections.

### Operator Markers

| Marker | Meaning |
|--------|---------|
| `*.` | Iterate (for each) |

### Format
```
<= *. %>([collection]) %<({result}) %:({current_item}) %@(loop_index)
    | %{sequence}: looping
<- [collection]
<* {current_item}<$([collection])*>
```

### Syntax Components

| Component | Meaning |
|-----------|---------|
| `%>([collection])` | The collection to iterate over |
| `%<({result})` | What each iteration produces |
| `%:({current_item})` | The loop variable name |
| `%@(1)` | Loop index (usually 1) |

### Key Annotations

1. **`%{sequence}: looping`** - Required sequence type marker

### Context Concept
The current loop item must be marked with `<*` and include
the source annotation `<$([collection])*>`:

```
<* {current_item}<$([collection])*>
    | %{ref_axes}: [_none_axis]
    | %{ref_element}: element_type
```

### Example
```
<= *. %>([concept lines]) %<({.ncd file written}) %:({concept line}) %@(1)
    /: Loop processes lines sequentially
    | %{sequence}: looping

<- [concept lines]
<* {concept line}<$([concept lines])*>
    | %{ref_axes}: [_none_axis]
    | %{ref_element}: dict
```

## Output

Return the formalized line(s) as a JSON object:

```json
{
  "formalized_line": "The complete formalized line with sequence annotation",
  "annotations_added": ["sequence"]
}
```

