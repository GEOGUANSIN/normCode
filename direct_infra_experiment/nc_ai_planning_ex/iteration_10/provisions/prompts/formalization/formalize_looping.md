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
- `depth`: Indentation level (0 = root, 1 = first child, etc.)
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For looping:

1. **Extract the iteration pattern** - Strip the `<=` marker and parse
2. **Identify collection and item** - What to iterate over, what each element is called
3. **Construct loop syntax** - With source, target, axis, and index
4. **Add flow index annotation** - Use the `flow_index` from input
5. **Add sequence type annotation** - `?{sequence}: looping`
6. **Calculate indentation** - Use `depth × 4 spaces`

## Indentation Rule

The formalized line MUST include proper indentation based on the `depth` field:

- **Indentation = depth × 4 spaces**
- `depth: 0` → No indentation (root level)
- `depth: 1` → 4 spaces
- `depth: 2` → 8 spaces
- `depth: 3` → 12 spaces

## Looping Syntax

### Format
```
[INDENTATION]<= *. %>([collection]) %<({result}) %:({item}) %@(1) | ?{flow_index}: X.X.X | ?{sequence}: looping
```

### Components

| Component | Meaning | Example |
|-----------|---------|---------|
| Indentation | Hierarchy level | 4 spaces per depth |
| `<=` | Functional concept marker | Already in input |
| `*.` | Iterate operator | Always `*.` |
| `%>([collection])` | Source collection | `%>([concept lines])` |
| `%<({result})` | What each iteration produces | `%<({processed line})` |
| `%:({item})` | Loop variable (current element) | `%:({concept line})` |
| `%@(1)` | Loop index (1 for outermost) | `%@(1)` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.1` |
| `?{sequence}:` | Sequence type | `?{sequence}: looping` |

### Pattern Recognition

| Natural Language | Collection | Item |
|-----------------|------------|------|
| "for each X in Y" | Y | X |
| "iterate over X" | X | (singular of X) |
| "loop through X" | X | (singular of X) |

## Examples

**Input (depth 1):**
```json
{
  "flow_index": "1.1",
  "content": "<= for each concept line in concept lines",
  "depth": 1,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
    <= *. %>([concept lines]) %<({processed}) %:({concept line}) %@(1) | ?{flow_index}: 1.1 | ?{sequence}: looping
```
(4 spaces indentation for depth 1)

**Explanation**: 
- Collection: `[concept lines]`
- Item: `{concept line}`
- Result: `{processed}` (generic, refined by child inferences)

---

**Input (depth 2):**
```json
{
  "flow_index": "2.1",
  "content": "<= iterate over parsed lines",
  "depth": 2,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
        <= *. %>([parsed lines]) %<({result}) %:({parsed line}) %@(1) | ?{flow_index}: 2.1 | ?{sequence}: looping
```
(8 spaces indentation for depth 2)

**Explanation**:
- Collection: `[parsed lines]`
- Item: `{parsed line}` (singular of collection)

---

**Input (depth 2):**
```json
{
  "flow_index": "1.2.1",
  "content": "<= loop through documents",
  "depth": 2,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
        <= *. %>([documents]) %<({result}) %:({document}) %@(1) | ?{flow_index}: 1.2.1 | ?{sequence}: looping
```
(8 spaces indentation for depth 2)

**Explanation**:
- Collection: `[documents]`
- Item: `{document}` (singular of "documents")

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what collection was identified, 2) what the loop item name is, 3) the indentation calculated",
  "result": "[INDENTATION]<= *. %>([collection]) %<({result}) %:({item}) %@(1) | ?{flow_index}: X.X.X | ?{sequence}: looping"
}
```

**Important**: 
- The `result` must be the complete formalized line as a single string
- Include the correct indentation (depth × 4 spaces) at the START of the line
- Include BOTH `?{flow_index}:` AND `?{sequence}: looping` annotations
- Collection uses `[...]` (relation), item uses `{...}` (object)
