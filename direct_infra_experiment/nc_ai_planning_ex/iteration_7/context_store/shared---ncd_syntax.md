# NormCode Draft (.ncd) Syntax Reference

## Core Markers

| Symbol | Name | Meaning |
|--------|------|---------|
| `<-` | Value Concept | Data (nouns) - inputs and outputs |
| `<=` | Functional Concept | Actions (verbs) - operations to execute |
| `<*` | Context Concept | In-loop state or context data |
| `:<:` | Output Marker | Marks the final result (root concept) |
| `:>:` | Input Marker | Marks external input |

## Inference Structure

```ncd
:<:{concept_to_infer} | ?{flow_index}: 1 | /: Description of goal
    <= _functional_concept_ | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {input_value_1}<:{1}> | ?{flow_index}: 1.2
    <- {input_value_2}<:{2}> | ?{flow_index}: 1.3
```

## Comment Types

### Syntactical Comments (`?{...}:`)
- `?{flow_index}:` - Step identifier (e.g., `1.2.3`)
- `?{sequence}:` - Agent sequence type
- `?{natural_language}:` - Natural language description

### Referential Comments (`%{...}:`)
- `%{paradigm}:` - Execution paradigm
- `%{file_location}:` - File path
- `%{prompt_location}:` - Prompt file path
- `%{ref_axes}:` - Reference tensor axes
- `%{ref_element}:` - Element type

### Derivation Comments
- `...:` - Source text (un-decomposed)
- `?:` - Question guiding decomposition
- `/:` - Description (complete)

## Sequence Types

### Semantic (LLM calls)
- `imperative` - Execute commands `::()` 
- `judgement` - Evaluate conditions `::< >`

### Syntactic (Free, deterministic)
- `assigning` - Data routing (`$.`, `$+`, `$-`)
- `grouping` - Collection creation (`&[{}]`, `&[#]`)
- `timing` - Execution control (`@:'`, `@:!`, `@.`)
- `looping` - Iteration (`*.`)

## Value Bindings

Explicit ordering of inputs:
```ncd
<- {first input}<:{1}> | ?{flow_index}: 1.2
<- {second input}<:{2}> | ?{flow_index}: 1.3
```

## Instance Markers

Reference specific instances:
```ncd
<= ::({prompt}<$({template})%>; {1}<$({input})%>)
```

