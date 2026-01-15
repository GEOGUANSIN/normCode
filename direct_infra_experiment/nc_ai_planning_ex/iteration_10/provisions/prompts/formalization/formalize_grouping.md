# Formalize Grouping Operator

Transform a natural language collection/bundling into formal grouping `&` syntax.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **grouping** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.1")
- `content`: The full line including marker (e.g., `"<= collect all results together"`)
- `depth`: Indentation level
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)
- `concept_type`: May be null (you're adding it)
- `concept_name`: May be null

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For grouping:

1. **Extract the operation** - Strip the `<=` marker from content
2. **Determine operator type** - `&[{}]` (labeled) or `&[#]` (flat)
3. **Identify items to group** - From context or explicit listing
4. **Add flow index** - Use the `flow_index` from input
5. **Add sequence type** - `?{sequence}: grouping`

## Grouping Operators

| Operator | Pattern in Content | Meaning | Syntax |
|----------|-------------------|---------|--------|
| `&[{}]` | "bundle", "combine with labels" | Group into dict | `&[{}] %>[{a}, {b}]` |
| `&[#]` | "collect all", "gather", "flatten" | Group into list | `&[#] %>[{a}, {b}]` |

### Format
```
<= &[#] %>[{item1}, {item2}] | ?{flow_index}: X.X.X | ?{sequence}: grouping
```

Or with axis creation:
```
<= &[{}] %>[{item1}, {item2}] %+(axis_name) | ?{flow_index}: X.X.X | ?{sequence}: grouping
```

## Examples

**Input (collect all):**
```json
{
  "flow_index": "1.1",
  "content": "<= collect all results together",
  "depth": 1,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= &[#] %>[{results}] | ?{flow_index}: 1.1 | ?{sequence}: grouping
```

**Explanation**: "collect all" → `&[#]` (flatten into list)

---

**Input (bundle with labels):**
```json
{
  "flow_index": "2.1",
  "content": "<= bundle inputs into single structure",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= &[{}] %>[{inputs}] | ?{flow_index}: 2.1 | ?{sequence}: grouping
```

**Explanation**: "bundle... into structure" → `&[{}]` (labeled dict)

---

**Input (gather multiple):**
```json
{
  "flow_index": "1.2.1",
  "content": "<= gather query and context and documents",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= &[{}] %>[{query}, {context}, {documents}] | ?{flow_index}: 1.2.1 | ?{sequence}: grouping
```

**Explanation**: Multiple items with "and" → `&[{}]` with explicit list

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) which operator was chosen (&[{}] or &[#]) and why, 2) what items were identified to group",
  "result": "<= &[X] %>[{items}] | ?{flow_index}: X.X.X | ?{sequence}: grouping"
}
```

**Important**: The `result` must be the complete formalized line as a single string, ready to be written to the `.ncd` file.
