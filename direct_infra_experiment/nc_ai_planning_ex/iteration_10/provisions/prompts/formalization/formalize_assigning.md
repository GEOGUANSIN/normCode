# Formalize Assigning Operator

Apply assigning `$` formalization syntax to this operator concept.

## Input

The concept line to formalize:
```json
$input_1
```

## Assigning Syntax Rules

Assigning operators handle variable binding and selection.

### Operator Markers

| Marker | Meaning | Example |
|--------|---------|---------|
| `$.` | Specification (select first valid) | `$. %>({result})` |
| `$%` | Abstraction (extract/abstract) | `$% %>({template})` |
| `$=` | Identity (pass through) | `$= %>({value})` |
| `$+` | Continuation (append) | `$+ %>({accumulator})` |
| `$-` | Derelation (remove from) | `$- %>({collection})` |

### Format
```
<= $. %>({source_concept})
    | %{sequence}: assigning
```

### Key Annotations

1. **`%{sequence}: assigning`** - Required sequence type marker

### Common Patterns

**Select first valid option:**
```
<= $. %>({result})
    | %{sequence}: assigning
<- {option_1}
<- {option_2}
<- {fallback}
```

**Extract from source:**
```
<= $% %>({data}) %:({field_name})
    | %{sequence}: assigning
<- {data}
```

## Output

Return JSON with thinking and result:

```json
{
  "thinking": "Explain what operator marker was identified and why",
  "result": "The complete formalized line with sequence annotation"
}
```
