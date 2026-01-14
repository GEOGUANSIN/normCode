# Judge Concept Type

Determine what type of concept this NormCode line represents.

## Input

You are given a parsed concept line from an .ncds file:

```json
$input_1
```

## Concept Types

Analyze the content and determine which type it is:

### Value Concepts (Semantic)
- **object** `{name}` - A thing, entity, data structure, singular value
- **relation** `[name]` - A collection, list, mapping, plural items  
- **proposition** `<name>` - A truth value, condition, boolean

### Function Concepts (Semantic)
- **imperative** `::()` - An action that transforms/produces something
- **judgement** `::<{}>` - An evaluation that returns true/false

### Syntactic Operators
- **assigning** `$.` `$%` `$=` - Variable binding, selection, abstraction
- **grouping** `&[{}]` `&[#]` - Bundling values together
- **timing** `@:'()` `@:!()` - Conditional execution gates
- **looping** `*.` - Iteration over collections

## Rules

1. Look at the `content` field to see the actual NormCode syntax
2. Look at the `inference_marker` for hints (`<=` = function, `<-` = value, `<*` = context)
3. If it starts with `::()` it's imperative; if `::<{}>` it's judgement
4. If content has `{name}` it's object, `[name]` it's relation, `<name>` it's proposition
5. Operators start with `$`, `&`, `@`, or `*`

## Output

Return JSON with thinking and result:

```json
{
  "thinking": "Brief explanation of why this type was chosen based on the content",
  "result": "object|relation|proposition|imperative|judgement|assigning|grouping|timing|looping"
}
```
