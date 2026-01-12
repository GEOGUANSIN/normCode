# Formalize Grouping Operator

Apply grouping `&` formalization syntax to this operator concept.

## Input

The concept line to formalize:
```json
$input_1
```

## Grouping Syntax Rules

Grouping operators bundle multiple values together.

### Operator Markers

| Marker | Meaning | Use Case |
|--------|---------|----------|
| `&[{}]` | Bundle into object | Collect sibling values into dict |
| `&[#]` | Bundle across axis | Collect along iteration axis |

### Format
```
<= &[{}] %>[{value_1}, {value_2}, ...] %+(new_axis)
    | %{sequence}: grouping
```

### Key Annotations

1. **`%{sequence}: grouping`** - Required sequence type marker

### Common Patterns

**Bundle values into dict:**
```
<= &[{}] %>[{extracted concepts}, [extracted operations], [extracted dependencies]]
    | %{sequence}: grouping
<- {extracted concepts}
<- [extracted operations]
<- [extracted dependencies]
```

**Create new axis from bundle:**
```
<= &[{}] %>[{a}, {b}, {c}] %+(items)
    | %{sequence}: grouping
```

### Note on Bundled Values
When bundled values are used as inputs to other inferences,
you may need `value_selectors` with `packed: true`.

## Output

Return the formalized line(s) as a JSON object:

```json
{
  "formalized_line": "The complete formalized line with sequence annotation",
  "annotations_added": ["sequence"]
}
```

