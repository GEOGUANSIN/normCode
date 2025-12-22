# NormCode Operators Reference

## Semantic Operators (LLM Calls)

### Imperative `::()` or `()`
Execute a command or action.
```ncd
<= ::({prompt}<$({template})%>; {1}<$({input})%>) | ?{sequence}: imperative
```

### Judgement `::< >`
Evaluate a truth condition.
```ncd
<= ::<{condition}> | ?{sequence}: judgement
```

---

## Syntactic Operators (Free, Deterministic)

### Assigning Operators (`$`)

| Operator | Purpose | Example |
|----------|---------|---------|
| `$.` | Select first valid | `$. %<[{option1}, {option2}]` |
| `$+` | Accumulate/append | `$+ %>({new_item})` |
| `$-` | Remove | `$- %>({item_to_remove})` |
| `$=` | Identity | `$= %>({existing_reference})` |

```ncd
<= $. %<[{primary_result}, {fallback_result}] | ?{sequence}: assigning
```

### Grouping Operators (`&`)

| Operator | Purpose | Example |
|----------|---------|---------|
| `&[#]` | Collect into ordered list | `&[#] %>({items})` |
| `&[{}]` | Group into labeled dict | `&[{}]` (children are fields) |

```ncd
<= &[#] %>({phase_outputs}) | ?{sequence}: grouping
```

### Timing Operators (`@`)

| Operator | Purpose | Example |
|----------|---------|---------|
| `@:'` | Execute if true | `@:' %>(<condition>)` |
| `@:!` | Execute if false | `@:! %>(<condition>)` |
| `@.` | Wait for dependency | `@. %>({dependency})` |

```ncd
<= ::(action)
    <= @:' %>(<validation_passed>)
    <* <validation_passed>
```

### Looping Operators (`*`)

| Operator | Purpose | Example |
|----------|---------|---------|
| `*.` | Iterate over collection | `*. %>({collection}) %<({element})` |

```ncd
<= *. %>({documents}) %<({summary}) | ?{sequence}: looping
<- {summary}
    <= ::(summarize this document)
    <- {document}*1
<* {document}<$({documents})*>
```

---

## Operator Syntax Patterns

### Basic Pattern
```
<= OPERATOR %>({source}) %<({destination})
```

- `%>()` - Source/input specification
- `%<()` - Destination/output specification

### With Bindings
```ncd
<= ::({1}<$({first_input})%>; {2}<$({second_input})%>)
<- {first_input}<:{1}>
<- {second_input}<:{2}>
```

