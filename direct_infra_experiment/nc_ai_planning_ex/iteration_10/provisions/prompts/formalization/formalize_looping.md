# Formalize Looping Operator

Transform a natural language iteration into formal looping `*` syntax.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **looping** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.1")
- `content`: The full line including marker (e.g., `"<= for each concept line in concept lines"`)
- `depth`: Indentation level
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)
- `concept_type`: May be null (you're adding it)
- `concept_name`: May be null

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For looping:

1. **Extract the iteration pattern** - Strip the `<=` marker and parse
2. **Identify collection and item** - What to iterate over, what each element is called
3. **Construct loop syntax** - With source, target, axis, and index
4. **Add flow index** - Use the `flow_index` from input
5. **Add sequence type** - `?{sequence}: looping`

## Looping Syntax

### Format
```
<= *. %>([collection]) %<({result}) %:({item}) %@(1) | ?{flow_index}: X.X.X | ?{sequence}: looping
```

### Components

| Component | Meaning | Example |
|-----------|---------|---------|
| `*.` | Iterate operator | Always `*.` |
| `%>([collection])` | Source collection | `%>([concept lines])` |
| `%<({result})` | What each iteration produces | `%<({processed line})` |
| `%:({item})` | Loop variable (current element) | `%:({concept line})` |
| `%@(1)` | Loop index (1 for outermost) | `%@(1)` |

### Pattern Recognition

| Natural Language | Collection | Item |
|-----------------|------------|------|
| "for each X in Y" | Y | X |
| "iterate over X" | X | (singular of X) |
| "loop through X" | X | (singular of X) |

## Examples

**Input:**
```json
{
  "flow_index": "1.1",
  "content": "<= for each concept line in concept lines",
  "depth": 1,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= *. %>([concept lines]) %<({processed}) %:({concept line}) %@(1) | ?{flow_index}: 1.1 | ?{sequence}: looping
```

**Explanation**: 
- Collection: `[concept lines]`
- Item: `{concept line}`
- Result: `{processed}` (generic, refined by child inferences)

---

**Input:**
```json
{
  "flow_index": "2.1",
  "content": "<= iterate over parsed lines",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= *. %>([parsed lines]) %<({result}) %:({parsed line}) %@(1) | ?{flow_index}: 2.1 | ?{sequence}: looping
```

**Explanation**:
- Collection: `[parsed lines]`
- Item: `{parsed line}` (singular of collection)

---

**Input:**
```json
{
  "flow_index": "1.2.1",
  "content": "<= loop through documents",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= *. %>([documents]) %<({result}) %:({document}) %@(1) | ?{flow_index}: 1.2.1 | ?{sequence}: looping
```

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what collection was identified, 2) what the loop item name is",
  "result": "<= *. %>([collection]) %<({result}) %:({item}) %@(1) | ?{flow_index}: X.X.X | ?{sequence}: looping"
}
```

**Important**: The `result` must be the complete formalized line as a single string, ready to be written to the `.ncd` file.
