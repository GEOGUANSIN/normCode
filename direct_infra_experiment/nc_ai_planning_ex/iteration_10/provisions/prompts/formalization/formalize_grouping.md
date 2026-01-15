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
- `depth`: Indentation level (0 = root, 1 = first child, etc.)
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For grouping:

1. **Extract the operation** - Strip the `<=` marker from content
2. **Determine operator type** - `&[{}]` (labeled) or `&[#]` (flat)
3. **Identify items to group** - From context or explicit listing
4. **Add flow index annotation** - Use the `flow_index` from input
5. **Add sequence type annotation** - `?{sequence}: grouping`
6. **Calculate indentation** - Use `depth × 4 spaces`

## Indentation Rule

The formalized line MUST include proper indentation based on the `depth` field:

- **Indentation = depth × 4 spaces**
- `depth: 0` → No indentation (root level)
- `depth: 1` → 4 spaces
- `depth: 2` → 8 spaces
- `depth: 3` → 12 spaces

## Grouping Operators

| Operator | Pattern in Content | Meaning | Syntax |
|----------|-------------------|---------|--------|
| `&[{}]` | "bundle", "combine with labels" | Group into dict | `&[{}] %>[{a}, {b}]` |
| `&[#]` | "collect all", "gather", "flatten" | Group into list | `&[#] %>[{a}, {b}]` |

### Format
```
[INDENTATION]<= &[#] %>[{item1}, {item2}] | ?{flow_index}: X.X.X | ?{sequence}: grouping
```

Or with axis creation:
```
[INDENTATION]<= &[{}] %>[{item1}, {item2}] %+(axis_name) | ?{flow_index}: X.X.X | ?{sequence}: grouping
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Indentation | Hierarchy level | 4 spaces per depth |
| `<=` | Functional concept marker | Already in input |
| `&[{}]` or `&[#]` | Grouping operator | Labeled or flat |
| `%>[{...}]` | Items to group | `%>[{a}, {b}]` |
| `%+(...)` | Create new axis (optional) | `%+(axis_name)` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.1` |
| `?{sequence}:` | Sequence type | `?{sequence}: grouping` |

## Examples

**Input (collect all, depth 1):**
```json
{
  "flow_index": "1.1",
  "content": "<= collect all results together",
  "depth": 1,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
    <= &[#] %>[{results}] | ?{flow_index}: 1.1 | ?{sequence}: grouping
```
(4 spaces indentation for depth 1)

**Explanation**: "collect all" → `&[#]` (flatten into list)

---

**Input (bundle with labels, depth 2):**
```json
{
  "flow_index": "2.1",
  "content": "<= bundle inputs into single structure",
  "depth": 2,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
        <= &[{}] %>[{inputs}] | ?{flow_index}: 2.1 | ?{sequence}: grouping
```
(8 spaces indentation for depth 2)

**Explanation**: "bundle... into structure" → `&[{}]` (labeled dict)

---

**Input (gather multiple, depth 2):**
```json
{
  "flow_index": "1.2.1",
  "content": "<= gather query and context and documents",
  "depth": 2,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
        <= &[{}] %>[{query}, {context}, {documents}] | ?{flow_index}: 1.2.1 | ?{sequence}: grouping
```
(8 spaces indentation for depth 2)

**Explanation**: Multiple items with "and" → `&[{}]` with explicit list

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) which operator was chosen (&[{}] or &[#]) and why, 2) what items were identified to group, 3) the indentation calculated",
  "result": "[INDENTATION]<= &[X] %>[{items}] | ?{flow_index}: X.X.X | ?{sequence}: grouping"
}
```

**Important**: 
- The `result` must be the complete formalized line as a single string
- Include the correct indentation (depth × 4 spaces) at the START of the line
- Include BOTH `?{flow_index}:` AND `?{sequence}: grouping` annotations
