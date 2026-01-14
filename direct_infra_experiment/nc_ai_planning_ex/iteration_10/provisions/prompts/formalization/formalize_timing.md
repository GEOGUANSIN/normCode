# Formalize Timing Operator

Apply timing `@` formalization syntax to this operator concept.

## Input

The concept line to formalize:
```json
$input_1
```

## Timing Syntax Rules

Timing operators control conditional execution (gates).

### Operator Markers

| Marker | Meaning | Use Case |
|--------|---------|----------|
| `@:'(<condition>)` | Execute if condition TRUE | Positive gate |
| `@:!(<condition>)` | Execute if condition FALSE | Negative gate |
| `@.(<action>)` | Execute after completion | Sequencing |

### Format
```
<= @:'(<condition concept>)
    | %{sequence}: timing
<* <condition concept>
```

### Key Annotations

1. **`%{sequence}: timing`** - Required sequence type marker

### Common Patterns

**Positive timing gate (execute if true):**
```
<= @:'(<is object type>)
    /: TIMING GATE: Only execute if type is object
<* <is object type>
```

**Negative timing gate (execute if false):**
```
<= @:!(<phase 1 already complete>)
    /: TIMING GATE: Only execute if phase NOT complete
<* <phase 1 already complete>
```

### Context Concept
The condition must reference a proposition (`<name>`) that's
marked with `<*` as the context concept for the timing gate.

## Output

Return JSON with thinking and result:

```json
{
  "thinking": "Explain what timing pattern was identified and why",
  "result": "The complete formalized line with sequence annotation"
}
```
